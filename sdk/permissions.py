from enum import Enum, auto

class AppPermission(Enum):
    # ──────────────────────────────────────────────
    # 🔐 Identity & User Info
    # ──────────────────────────────────────────────
    READ_USERNAME = auto()  # Read the logged-in user's username
    READ_USER_ID = auto()   # Read the user's UUID or internal ID

    # ──────────────────────────────────────────────
    # 🤵 User Field Access
    # ──────────────────────────────────────────────
    READ_USER_FIELD =  auto()
    WRITE_USER_FIELD = auto()
    DELETE_USER_FIELD = auto()

    # ──────────────────────────────────────────────
    # 💰 Economy
    # ──────────────────────────────────────────────
    READ_GBALANCE = auto()     # View current user's gBalance
    MODIFY_GBALANCE = auto()   # Add or subtract from user's gBalance

    # ──────────────────────────────────────────────
    # 🔊 User Experience Features
    # ──────────────────────────────────────────────
    PLAY_SOUNDS = auto()              # Play sounds via AppBridge
    USE_TYPING_VISUALIZER = auto()    # Access live keystroke visualizer

    # ──────────────────────────────────────────────
    # ⚙️ App Settings + Returns
    # ──────────────────────────────────────────────
    READ_APP_SETTINGS = auto()   # Read custom config stored for app
    WRITE_APP_SETTINGS = auto()  # Write config/settings for app
    SET_RETURN_VALUE = auto()    # Return values for launch logs, etc.

    # ──────────────────────────────────────────────
    # 📜 Logging
    # ──────────────────────────────────────────────
    LOG_INFO = auto()    # Post info logs visible in gNet launcher
    LOG_ERRORS = auto()  # Post errors/warnings to app logs

    # ──────────────────────────────────────────────
    # 📁 File I/O (Scoped)
    # ──────────────────────────────────────────────
    READ_APP_FILES = auto()     # Read files within its own app folder
    WRITE_APP_FILES = auto()    # Write files inside its own app folder

    READ_GLOBAL_FILES = auto()  # Read any file outside app folder
    WRITE_GLOBAL_FILES = auto() # Modify files outside app folder (very sensitive)

    MODIFY_APP_METADATA = auto()  
    # Allows modifying *non-critical* metadata like:
    # - semantic version (major/minor/patch individually)
    # - display name or icon path
    # - developer name or app description
    # Does NOT allow editing app_id, UUID, or declared permissions

    # ──────────────────────────────────────────────
    # 🌐 Network Permissions
    # ──────────────────────────────────────────────
    ACCESS_LOCAL_NETWORK = auto()   # Access 127.0.0.1 or LAN IPs
    ACCESS_INTERNET = auto()        # Access external hosts/domains

    # ──────────────────────────────────────────────
    # ⚠️ Dangerous Escalations (Require Dev Mode)
    # ──────────────────────────────────────────────
    EXECUTE_EXTERNAL_BINARIES = auto()  # subprocess / .exe launching
    ACCESS_PYTHON_NATIVE_APIS = auto()  # direct open/os/import usage
    SPAWN_SUBPROCESSES = auto()         # fork subprocesses or run code async
    INSPECT_OTHER_APPS = auto()         # read/modify folders of other apps
