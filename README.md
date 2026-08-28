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
- **App Store** — the Apps page has an "Installed" list plus a Store tab that
  loads apps from the `apps/` folder of a GitHub repository (each app folder is
  downloaded into `apps/`), so anyone can distribute apps through the repo
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
  transaction logs, and debit-card management. Login supports "Remember me"
  so you can skip password entry on the next launch
- **UI** — dark-themed launcher with Home, Apps, Settings, and Profile pages
  styled by a shared `style.qss` stylesheet

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

### Installing apps from the store

1. Open the **Apps** page and go to the **Store** tab.
2. The default store points at `ToClickx/gnet` on GitHub (branch `main`).
3. Press **Load** to fetch the list of app folders in that repo's `apps/`
   directory, then press **Install** next to any app to download it.
4. Change the owner/repo/branch in **Settings** to use your own GitHub repo.

See `apps/testbridge/main.py` for a runnable example that exercises the whole
bridge (sandbox files, user fields, network, gBalance, permission denials).

### Bundled apps

| App | What it does |
| --- | --- |
| `calculator` | Four-function calculator |
| `notes` | Sandbox notes with a list of your saved notes (new/save/delete) |
| `todo` | Per-user task list stored via user fields |
| `stopwatch` | Lap-capable stopwatch |
| `coinflip` | Bet on heads/tails and win 2x your bet |
| `luckynumbers` | Bet gBalance on 1-10 and win 5x your bet |
| `stonks` | Buy/sell virtual stocks whose prices drift, so you can grow or lose your gBalance |

Every new user starts with a `default` debit card, so the money games work
right away. Apps spend through `bridge.spend_gbalance(...)` and collect
winnings through `bridge.award_gbalance(...)`, which is capped per transaction
and per day so nothing can print money forever.

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
│   ├── calculator/        # Four-function calculator
│   ├── notes/             # Notes with saved-note manager
│   ├── todo/              # Per-user task list
│   ├── stopwatch/         # Lap stopwatch
│   ├── coinflip/          # Bet on coin flips
│   ├── luckynumbers/      # Number lottery game
│   ├── stonks/            # Stock trading game
│   └── testbridge/        # Example app exercising the SDK
├── core/
│   ├── app_discovery.py  # Finds and loads apps at startup
│   ├── app_store.py      # Fetches + downloads apps from a GitHub repo
│   └── app_manager.py    # Installed-app list, install/uninstall, refresh
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