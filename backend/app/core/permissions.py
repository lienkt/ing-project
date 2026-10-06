"""Role policy, loaded once per process; unmapped endpoints are denied."""

from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, ConfigDict, model_validator

POLICY_PATH = Path(__file__).resolve().parents[2] / "config" / "permissions.json"


class PermissionPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    permissions: list[str]
    roles: dict[str, list[str]]
    api: dict[str, str]

    @model_validator(mode="after")
    def validate_references(self):
        declared = set(self.permissions)
        if not declared or len(declared) != len(self.permissions):
            raise ValueError("Permissions must be nonempty and unique")
        for name in declared:
            if not name or name.strip() != name:
                raise ValueError("Invalid permission name")
        for role, grants in self.roles.items():
            if not role or not set(grants) <= declared:
                raise ValueError("Invalid role or unknown permission in role grants")
        for endpoint, permission in self.api.items():
            method, separator, path = endpoint.partition(" ")
            if (
                not separator
                or method not in {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"}
                or not path.startswith("/api/")
                or permission not in declared
            ):
                raise ValueError("Invalid API endpoint or unknown permission")
        return self

    def grants(self, roles: list[str]) -> set[str]:
        return {permission for role in roles for permission in self.roles.get(role, [])}


@lru_cache
def load_policy() -> PermissionPolicy:
    return PermissionPolicy.model_validate_json(POLICY_PATH.read_text())
