"""Device tracker for Geely Galaxy vehicles.

车厂在 `/vc/app/v1/vehicle/control/status` 的响应里本来就带车辆位置
（`vehicleLocationStatus`），只是上游集成没有解析它。这里把它暴露成标准的
device_tracker 实体：可以显示在地图上、可以匹配 zone（在家/离家）。

注意：经纬度**不是加密的**，车厂以 1/3600000 度为单位的整数返回，
除以 LOCATION_COORD_SCALE 即为度数。
"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN, LOCATION_COORD_SCALE

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the vehicle location tracker from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([GeelyVehicleLocationTracker(coordinator, entry)])


class GeelyVehicleLocationTracker(CoordinatorEntity, TrackerEntity):
    """车辆位置。"""

    _attr_has_entity_name = True
    _attr_name = "车辆位置"

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the tracker."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_vehicle_location"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info, 与其它实体共用同一个「车辆」设备。"""
        vehicle_info = (
            self.coordinator.data.get("vehicle_info", {})
            if self.coordinator.data
            else {}
        )
        vin = vehicle_info.get("vin", "unknown")
        model = vehicle_info.get("seriesNameVs", "吉利银河")

        return {
            "identifiers": {(DOMAIN, vin)},
            "name": f"{model}",
            "manufacturer": "吉利汽车",
            "model": model,
        }

    @property
    def _location(self) -> dict[str, Any]:
        """返回原始的 vehicleLocationStatus 字段。"""
        if not self.coordinator.data:
            return {}
        status = self.coordinator.data.get("vehicle_status") or {}
        return status.get("vehicleLocationStatus") or {}

    @staticmethod
    def _to_degrees(raw: Any, is_latitude: bool) -> float | None:
        """把车厂返回的整数换算成度数。

        车厂单位是 1/3600000 度，直接相除即可，不涉及解密。
        任何异常都返回 None，避免因单个字段异常导致实体创建失败。

        额外做合理性校验：换算结果必须落在合法经纬度范围内，且不能是
        (0, 0)（车厂常用它表示「无定位」）。这样即使某个车型的字段含义
        与预期不同，也只会显示「未知」，而不会在地图上标出一个错误位置。
        """
        if raw is None or raw == "":
            return None
        try:
            value = float(raw) / LOCATION_COORD_SCALE
        except (TypeError, ValueError):
            return None

        limit = 90.0 if is_latitude else 180.0
        if not (-limit <= value <= limit):
            _LOGGER.warning(
                "车辆位置字段超出合法范围，已忽略: %s=%s",
                "latitude" if is_latitude else "longitude",
                raw,
            )
            return None
        if value == 0:
            # 0 基本可确定是「无定位」占位值，而非真的在几内亚湾
            return None
        return round(value, 6)

    @property
    def latitude(self) -> float | None:
        """Return latitude value of the vehicle."""
        return self._to_degrees(self._location.get("latitude"), True)

    @property
    def longitude(self) -> float | None:
        """Return longitude value of the vehicle."""
        return self._to_degrees(self._location.get("longitude"), False)

    @property
    def source_type(self) -> SourceType:
        """Return the source type."""
        return SourceType.GPS

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """暴露车厂对定位质量的声明，便于排查。"""
        loc = self._location
        attrs: dict[str, Any] = {}

        altitude = loc.get("altitude")
        if altitude not in (None, ""):
            try:
                attrs["altitude"] = float(altitude)
            except (TypeError, ValueError):
                pass

        # 车厂声明坐标是否已做火星坐标（GCJ-02）偏移。
        # false 表示是原始坐标，可以直接交给 HA，无需转换。
        if "marsCoordinates" in loc:
            attrs["mars_coordinates"] = loc.get("marsCoordinates")

        # 车厂声明本次定位是否可信
        if "posCanBeTrusted" in loc:
            attrs["position_trusted"] = loc.get("posCanBeTrusted")

        return attrs
