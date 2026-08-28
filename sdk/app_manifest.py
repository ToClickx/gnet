import json
from uuid import UUID
from typing import List
from enum import Enum
from sdk.permissions import AppPermission  # use the enum you defined earlier

class SemanticVersion:
    def __init__(self, major: int, minor: int, patch: int):
        self.major = major
        self.minor = minor
        self.patch = patch

    def __str__(self):
        return f"{self.major}.{self.minor}.{self.patch}"

    def to_dict(self):
        return {
            "major": self.major,
            "minor": self.minor,
            "patch": self.patch
        }

    @classmethod
    def from_dict(cls, d):
        return cls(d["major"], d["minor"], d["patch"])

class AppManifest:
    def __init__(
        self,
        app_id: str,
        uuid: UUID,
        display_name: str,
        description: str,
        developer: str,
        version: SemanticVersion,
        icon_path: str,
        entry_point: str,
        permissions: List[AppPermission]
    ):
        self.app_id = app_id                      # Required internal identifier (folder name or slug)
        self.uuid = uuid                          # Locked unique app ID
        self.display_name = display_name          # Human-friendly name
        self.description = description            # Short description
        self.developer = developer                # Dev name or org
        self.version = version                    # Semantic versioning
        self.icon_path = icon_path                # Relative to app folder
        self.entry_point = entry_point            # e.g. "main.py"
        self.permissions = permissions            # AppPermission enum list

    def to_dict(self):
        return {
            "app_id": self.app_id,
            "uuid": str(self.uuid),
            "display_name": self.display_name,
            "description": self.description,
            "developer": self.developer,
            "version": self.version.to_dict(),
            "icon_path": self.icon_path,
            "entry_point": self.entry_point,
            "permissions": [p.name for p in self.permissions]
        }

    @classmethod
    def from_dict(cls, d: dict):
        return cls(
            app_id=d["app_id"],
            uuid=UUID(d["uuid"]),
            display_name=d["display_name"],
            description=d.get("description", ""),
            developer=d.get("developer", ""),
            version=SemanticVersion.from_dict(d["version"]),
            icon_path=d.get("icon_path", ""),
            entry_point=d.get("entry_point", "main.py"),
            permissions=[AppPermission[p] for p in d.get("permissions", [])]
        )

    @classmethod
    def from_file(cls, path: str):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def save_to_file(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=4)
