import os
import importlib.util
from sdk.app_base import GNetAppBase

def discover_apps():
    apps = []
    apps_dir = "apps"

    for folder in os.listdir(apps_dir):
        folder_path = os.path.join(apps_dir, folder)
        main_py = os.path.join(folder_path, "main.py")

        if os.path.isdir(folder_path) and os.path.isfile(main_py):
            spec = importlib.util.spec_from_file_location(f"apps.{folder}.main", main_py)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find the app class that subclasses GNetAppBase
            app_class = None
            for attr_name in dir(module):
                obj = getattr(module, attr_name)
                try:
                    if issubclass(obj, GNetAppBase) and obj is not GNetAppBase:
                        app_class = obj
                        break
                except TypeError:
                    continue

            if app_class:
                apps.append({
                    "name": getattr(app_class, "app_name", folder),
                    "version": getattr(app_class, "app_version", "0.0.0"),
                    "description": getattr(app_class, "app_description", ""),
                    "icon": getattr(app_class, "app_icon", None),
                    "class": app_class,
                })

    return apps