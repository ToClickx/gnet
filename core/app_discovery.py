import os
import importlib.util
from sdk.app_base import GNetAppBase
from sdk.app_manifest import AppManifest


def _load_manifest(app_dir: str):
    manifest_path = os.path.join(app_dir, "manifest.json")
    if os.path.isfile(manifest_path):
        try:
            return AppManifest.from_file(manifest_path)
        except Exception:
            return None
    return None


def discover_apps():
    apps = []
    apps_dir = "apps"

    for folder in os.listdir(apps_dir):
        folder_path = os.path.join(apps_dir, folder)
        main_py = os.path.join(folder_path, "main.py")

        if os.path.isdir(folder_path) and os.path.isfile(main_py):
            spec = importlib.util.spec_from_file_location(f"apps.{folder}.main", main_py)
            module = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(module)
            except Exception:
                module = None

            app_class = None
            if module is not None:
                for attr_name in dir(module):
                    obj = getattr(module, attr_name)
                    try:
                        if issubclass(obj, GNetAppBase) and obj is not GNetAppBase:
                            app_class = obj
                            break
                    except TypeError:
                        continue

            manifest = _load_manifest(folder_path)

            # prefer manifest.json metadata when present
            if manifest:
                name = manifest.display_name
                version = str(manifest.version)
                description = manifest.description
            else:
                name = getattr(app_class, "app_name", "Untitled App") if app_class else "Untitled App"
                version = getattr(app_class, "app_version", "0.0.0") if app_class else "0.0.0"
                description = getattr(app_class, "app_description", "") if app_class else ""

            apps.append({
                "id": folder,
                "name": name,
                "version": version,
                "description": description,
                "icon": getattr(app_class, "app_icon", None) if app_class else None,
                "folder": folder_path,
                "manifest": manifest,
                "class": app_class,
            })

    return apps