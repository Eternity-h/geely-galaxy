# Geely Galaxy — Home Assistant Integration

A Home Assistant custom integration for Geely Galaxy (吉利银河) vehicles: status monitoring,
remote control, charging management and daily check-in.

> **This is an independently maintained fork of
> [lyj5812/geely-galaxy](https://github.com/lyj5812/geely-galaxy).**
> Upstream has not been updated since 2026-08 (three open issues, none answered). This fork
> fixes several defects that made the integration unusable, and is released on its own
> schedule. Original code copyright belongs to the upstream author — see [LICENSE](LICENSE).

Current version: **1.0.1**

---

## Fixes over upstream

| Problem | Impact | Status |
|---|---|---|
| Captcha proxy returned 502 with recent aiohttp | Slider captcha never loaded; login could not proceed | Fixed |
| Wrong port in the captcha page URL | Browser sent to `:8123`; broken when HA runs on another port | Fixed |
| Reflected XSS in the captcha view | Unauthenticated endpoint; could leak the HA session token | Fixed |
| Vehicle access token written to the log | Vehicle-control credentials readable from HA logs | Fixed |
| Unbounded captcha result cache | Unauthenticated requests could grow memory without limit | Fixed |
| Proxy skipped TLS verification, wildcard CORS | Could be abused as an anonymous relay | Fixed |
| Battery level entity failed to be created | `ValueError` on every start; entity missing | Fixed |

---

## Features

- **Status** — battery, range, odometer, interior/exterior temperature, PM2.5, average consumption, lock and climate state
- **Remote control** — lock/unlock, find-my-car, windows, climate, defrost, air purification
- **Charging** — charge state, power, voltage, current, charging history, home charger
- **Other** — sentry mode, scheduled charging, daily check-in

## Supported vehicles

- **Geely Galaxy 星舰7 EM-i** — verified working with this fork
- **Geely Galaxy L7 / geely2 platform** — supported per upstream

Available entities differ by model. Vehicles on the XCHANGER channel (e.g. L7) additionally expose
fuel level, fuel range and tyre pressure, but do not expose sentry mode or scheduled charging.

---

## Installation

### Via HACS (recommended)

This integration is **not in the HACS default list** — add it as a custom repository:

1. Make sure [HACS](https://hacs.xyz/) is installed
2. HACS → **Integrations** → ⋮ (top right) → **Custom repositories**
3. Enter `https://github.com/Eternity-h/geely-galaxy`, category **Integration**
4. Search for "Geely Galaxy" and download
5. Restart Home Assistant

### Manual

Copy the whole `custom_components/geely_galaxy/` directory into your Home Assistant
`custom_components/` folder, then restart.

> ⚠️ **Do not use both methods at once.** HACS and manual installs write to the same directory
> and will overwrite each other.

---

## Configuration

Go to **Settings → Devices & Services → Add Integration** and search for "Geely Galaxy".

| Login method | Notes |
|---|---|
| **SMS code** | Phone number → slider captcha → SMS code (recommended) |
| **Token** | Requires `refresh_token` and `device_sn` captured from the app |
| **Password** | Requires the SM4-encrypted password |

---

## Entities

On the verified model (星舰7 EM-i) the integration creates **34 entities**:

| Type | Count | Contents |
|---|---|---|
| Sensors | 21 | model, VIN, check-in state, battery level, range, odometer, time to full, interior/exterior temperature, interior PM2.5, average consumption, lock state, climate state, charging state/power/voltage/current, last charge SOC, last charge energy, sentry mode, scheduled charging |
| Switches | 1 | sentry mode |
| Buttons | 12 | lock, unlock, find car, climate on/off, window close, window vent, defrost on/off, purifier on/off, daily check-in |

Each home charger also creates its own device with charging sensors.

---

## ⚠️ Important notes

**Single session per account (most important)**
A Geely account allows only one active session at a time. The integration polls on a fixed
interval (60 s by default) and **may sign your phone app out**. If that happens, increase the
interval — edit `custom_components/geely_galaxy/const.py`:

```python
DEFAULT_SCAN_INTERVAL = 300   # recommended ≥ 300; default is 60
```

then restart Home Assistant. A longer interval signs you out less often, at the cost of slower
state updates.

**Signing keys**
The app-level signing keys embedded in this integration were extracted from the official app.
If Geely rotates them, the integration stops working until it is updated.

**Rate limiting**
Frequent calls may be throttled server-side. Do not set the polling interval very low.

**Credential storage**
The refresh token is stored in plain text in the HA config entry, as with most HA integrations.
Mind the permissions on your HA config directory.

---

## Troubleshooting

1. Check the HA log (**Settings → System → Logs**) and filter for `geely_galaxy`
2. Open an [issue](https://github.com/Eternity-h/geely-galaxy/issues)

> ⚠️ **Check your log for tokens before posting it.** This fork stopped logging tokens as of
> 1.0.1, but older versions — or DEBUG logging — may still print credential material.

---

## Development

This integration is based on reverse engineering of the Geely Galaxy app API. Related projects:

- [lyj5812/geely-galaxy](https://github.com/lyj5812/geely-galaxy) — upstream
- [suyunkai/geely-galaxy-assistant](https://github.com/suyunkai/geely-galaxy-assistant) — Qinglong panel script with broader command coverage

---

## License

[MIT](LICENSE). Original copyright belongs to the upstream author; modifications in this fork are
released under the same license.
