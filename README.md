# gNet 2

A desktop app platform built with Python and PyQt6. gNet treats every installed
program as a *sandboxed app*: each app declares the permissions it needs in a
manifest, and can only touch user data, files, the network, and the system
through a locked-down `AppBridge`.

> **Built with AI assistance.** This project was developed with the help of an
> AI coding assistant. The code is deterministic and has been reviewed by a
> human.

## What it does

- **App model** — apps are plain folders under `apps/` with a `main.py` entry
  point, discovered and loaded at launch
- **Manifest system** — each app ships a `manifest.json` declaring its stable
  `uuid`, semantic version, developer, and the `AppPermission`s it requests
- **Permission-gated `AppBridge`** — the only way an app reaches the outside
  world. It enforces:
  - File I/O *inside* the app's own sandbox vs. global paths
  - Network access split into local vs. internet
  - Identity / account fields (`READ_USERNAME`, `READ_USER_FIELD`, ...)
  - An in-app economy (`gBalance`) with per-app spending caps and card-based
    limits
  - Violations are logged per-app, so apps can never silently exceed their
    grants
- **User accounts** — password-hashed login, persistent profile/app data,
  transaction logs, and debit-card management
- **UI** — dark-themed launcher with Home, Apps, Settings, and Profile pages
  (`qdarktheme` + a shared QSS stylesheet)

## The permission model

`AppPermission` (`sdk/permissions.py`) is a granular enum, e.g.:

| Category | Permissions |
| --- | --- |
| Identity | `READ_USERNAME`, `READ_USER_ID` |
| User fields | `READ/WRITE/DELETE_USER_FIELD` |
| Economy | `READ_GBALANCE`, `MODIFY_GBALANCE` |
| File I/O | `READ/WRITE_APP_FILES`, `READ/WRITE_GLOBAL_FILES` |
| Network | `ACCESS_LOCAL_NETWORK`, `ACCESS_INTERNET` |
| Escalation (dev-mode) | `EXECUTE_EXTERNAL_BINARIES`, `SPAWN_SUBPROCESSES`, ... |

`AppBridge` is constructed per-app with only the app's granted permissions —
anything unsupported raises `PermissionError` and is recorded to the app's log
before the request can have an effect.

## Writing an app

1. Create a folder under `apps/` (e.g. `apps/mycoolapp/`).
2. Add `main.py` with a class subclassing `GNetAppBase`:

```python
from sdk.app_base import GNetAppBase

class App(GNetAppBase):
    app_name = "My Cool App"
    app_version = "1.0.0"
    app_description = "Does a thing."

    def main(self):
        # self.bridge is an AppBridge already scoped to your app
        print(self.bridge.get_username())
```

3. Run `python main.py` — the app is discovered automatically.

See `apps/testbridge/main.py` for a runnable example that exercises the whole
bridge (sandbox files, user fields, network, gBalance, permission denials).

## Getting Started

```bash
pip install -r requirements.txt
python main.py
```

## Project Layout

```
gNet 2/
├── main.py               # Launcher entry point
├── requirements.txt
├── style.qss             # Global stylesheet
├── apps/
│   └── testbridge/       # Example app exercising the SDK
├── core/
│   └── app_discovery.py  # Finds and loads apps at startup
├── sdk/
│   ├── app_base.py       # GNetAppBase — all apps subclass this
│   ├── app_bridge.py     # Permission-enforcing sandbox API
│   ├── app_manifest.py   # Manifest + semantic versioning
│   └── permissions.py    # AppPermission enum
├── ui/                   # Launcher pages (login, app browser, settings...)
├── user/                 # Account, storage, debit cards, manager
└── assets/               # Icons and sounds
```

## License

MIT