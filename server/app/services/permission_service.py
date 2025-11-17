"""
Permission management utilities based on user's permission_group.

Groups and implied capabilities (default):
- admin: full access, can manage users, read/write/delete
- manager: read/write/delete
- user: read/write
- viewer: read-only
"""
from typing import Dict
from app.models.user import User


class PermissionManager:
    GROUP_CAPABILITIES: Dict[str, Dict[str, bool]] = {
        "admin": {
            "read": True,
            "write": True,
            "delete": True,
            "manage_users": True,
            "all_data": True,
        },
        "manager": {
            "read": True,
            "write": True,
            "delete": True,
            "manage_users": False,
            "all_data": True,
        },
        "user": {
            "read": True,
            "write": True,
            "delete": False,
            "manage_users": False,
            "all_data": False,
        },
        "viewer": {
            "read": True,
            "write": False,
            "delete": False,
            "manage_users": False,
            "all_data": False,
        },
    }

    @classmethod
    def _capabilities(cls, group: str) -> Dict[str, bool]:
        return cls.GROUP_CAPABILITIES.get(group.lower(), cls.GROUP_CAPABILITIES["viewer"]) if group else cls.GROUP_CAPABILITIES["viewer"]

    @classmethod
    def get_permission_info(cls, user: User) -> Dict[str, bool]:
        caps = cls._capabilities(user.permission_group)
        return {
            "group": user.permission_group,
            **caps,
        }

    @classmethod
    def can_access_all_data(cls, user: User) -> bool:
        return cls._capabilities(user.permission_group).get("all_data", False)

    @classmethod
    def check_table_access(cls, user: User, table_name: str) -> bool:
        # For now, table-level access is equivalent to read capability.
        return cls._capabilities(user.permission_group).get("read", False)
