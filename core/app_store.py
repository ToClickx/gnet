import os
import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPS_DIR = os.path.join(BASE_DIR, "apps")

API = "https://api.github.com"
RAW = "https://raw.githubusercontent.com"


class StoreError(Exception):
    pass


class RemoteApp:
    def __init__(self, name: str, owner: str, repo: str, branch: str, files: list):
        self.name = name
        self.owner = owner
        self.repo = repo
        self.branch = branch
        self.files = files  # list of {"path": ..., "download_url": ...}

    def download_url(self, path: str) -> str:
        return f"{RAW}/{self.owner}/{self.repo}/{self.branch}/{path}"


def _api_get(url: str, timeout: int = 20):
    import requests
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        raise StoreError(f"GitHub request failed: {e}")


def list_store_apps(owner: str, repo: str, branch: str) -> list[RemoteApp]:
    """List app folders under apps/ in the remote repo."""
    try:
        tree = _api_get(f"{API}/repos/{owner}/{repo}/git/trees/{branch}?recursive=1")
    except StoreError:
        tree = _api_get(f"{API}/repos/{owner}/{repo}/contents/apps")
        return _from_contents(owner, repo, branch, tree)

    entries = tree.get("tree", [])
    prefix = "apps/"
    apps = {}
    for entry in entries:
        path = entry.get("path", "")
        if not path.startswith(prefix):
            continue
        parts = path.split("/")
        # skip files directly under apps/ (not inside a subfolder)
        if len(parts) < 3:
            continue
        app_name = parts[1]
        if entry.get("type") == "tree":
            if app_name not in apps:
                apps[app_name] = []
            continue
        if app_name not in apps:
            apps[app_name] = []
        if entry.get("type") == "blob":
            apps[app_name].append({
                "path": path,
                "download_url": f"{RAW}/{owner}/{repo}/{branch}/{path}",
            })

    result = []
    for name, files in apps.items():
        if not any(f["path"].endswith("main.py") for f in files):
            continue
        result.append(RemoteApp(name, owner, repo, branch, files))
    return result


def _from_contents(owner, repo, branch, contents):
    result = []
    for item in contents or []:
        if item.get("type") != "dir":
            continue
        name = item.get("name")
        files = _collect_folder(owner, repo, branch, item.get("path"))
        if any(f["path"].endswith("main.py") for f in files):
            result.append(RemoteApp(name, owner, repo, branch, files))
    return result


def _collect_folder(owner, repo, branch, folder_path: str, timeout: int = 20):
    import requests
    api_url = f"{API}/repos/{owner}/{repo}/contents/{folder_path}"
    try:
        resp = requests.get(api_url, timeout=timeout)
        resp.raise_for_status()
        entries = resp.json()
    except requests.RequestException as e:
        raise StoreError(f"Failed to list {folder_path}: {e}")

    files = []
    for entry in entries:
        if entry.get("type") == "file":
            files.append({
                "path": entry["path"],
                "download_url": entry.get("download_url"),
            })
        elif entry.get("type") == "dir":
            files.extend(_collect_folder(owner, repo, branch, entry["path"]))
    return files


def download_app(app: RemoteApp, target_dir: str = APPS_DIR) -> str:
    """Download a remote app into the local apps directory. Returns its path."""
    import requests
    dest = os.path.join(target_dir, app.name)
    os.makedirs(dest, exist_ok=True)

    for file in app.files:
        rel = file["path"]
        # strip leading apps/<name>/ prefix
        parts = rel.split("/")
        if len(parts) > 2 and parts[0] == "apps" and parts[1] == app.name:
            rel = "/".join(parts[2:])
        if not rel:
            continue
        if rel == ".gitignore" or "__pycache__" in rel:
            continue
        url = file.get("download_url") or app.download_url(file["path"])
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
        except requests.RequestException as e:
            raise StoreError(f"Failed to download {rel}: {e}")

        out_path = os.path.join(dest, rel)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "wb") as f:
            f.write(resp.content)

    # require a main.py to be a valid app
    if not os.path.isfile(os.path.join(dest, "main.py")):
        _cleanup(dest)
        raise StoreError(f"Downloaded app '{app.name}' has no main.py entry point.")
    return dest


def _cleanup(path: str):
    import shutil
    if os.path.isdir(path):
        shutil.rmtree(path, ignore_errors=True)