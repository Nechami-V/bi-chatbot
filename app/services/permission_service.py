"""
Permission system for controlling access to different data tables
Future-ready for table-specific permissions
"""

from typing import Dict, List, Set
from app.models.user import User

class PermissionManager:
    """Manages user permissions and table access control"""
    
    # Define available tables in the system
    AVAILABLE_TABLES = {
        "clients", "orders", "sales", "items", 
        "customers", "products", "reports"
    }
    
    # Permission groups and their allowed tables
    # Currently all groups have access to all tables
    # Future: will be table-specific per group
    PERMISSION_GROUPS = {
        "admin": AVAILABLE_TABLES,  # Full access
        "sales_manager": AVAILABLE_TABLES,  # Currently full access
        "sales": AVAILABLE_TABLES,  # Currently full access  
        "marketing": AVAILABLE_TABLES,  # Currently full access
        "finance": AVAILABLE_TABLES,  # Currently full access
        "readonly": AVAILABLE_TABLES,  # Currently full access (read-only will be handled differently)
    }
    
    @classmethod
    def check_table_access(cls, user: User, table_name: str) -> bool:
        """
        Check if user has access to specific table
        Args:
            user: User object
            table_name: Name of table to check access for
        Returns:
            True if user has access, False otherwise
        """
        if not user or not user.permission_group:
            return False
        
        # Get allowed tables for user's permission group
        allowed_tables = cls.PERMISSION_GROUPS.get(user.permission_group, set())
        
        # Check if table is in allowed list
        return table_name.lower() in allowed_tables
    
    @classmethod
    def get_user_accessible_tables(cls, user: User) -> Set[str]:
        """Get list of tables user can access"""
        if not user or not user.permission_group:
            return set()
        
        return cls.PERMISSION_GROUPS.get(user.permission_group, set())
    
    @classmethod
    def is_manager(cls, user: User) -> bool:
        """Check if user is a manager"""
        return user and user.is_manager
    
    @classmethod
    def can_access_all_data(cls, user: User) -> bool:
        """Check if user has admin-level access"""
        return user and user.permission_group == "admin"
    
    @classmethod
    def get_permission_info(cls, user: User) -> Dict:
        """Get detailed permission information for user"""
        if not user:
            return {
                "has_access": False,
                "permission_group": None,
                "accessible_tables": [],
                "is_manager": False,
                "is_admin": False
            }
        
        return {
            "has_access": True,
            "permission_group": user.permission_group,
            "accessible_tables": list(cls.get_user_accessible_tables(user)),
            "is_manager": cls.is_manager(user),
            "is_admin": cls.can_access_all_data(user),
            "user_info": {
                "id": user.id,
                "name": user.full_name,
                "email": user.email
            }
        }

# Permission groups for future table restrictions
FUTURE_PERMISSION_SETUP = {
    "admin": {
        "tables": ["clients", "orders", "sales", "items", "customers", "products", "reports"],
        "description": "Full system access"
    },
    "sales_manager": {
        "tables": ["clients", "orders", "sales", "customers"],
        "description": "Sales department management"
    }, 
    "sales": {
        "tables": ["clients", "orders", "customers"],
        "description": "Sales team access"
    },
    "marketing": {
        "tables": ["customers", "products", "reports"],
        "description": "Marketing team access"
    },
    "finance": {
        "tables": ["orders", "sales", "reports"], 
        "description": "Finance team access"
    },
    "readonly": {
        "tables": ["reports"],
        "description": "Read-only access to reports"
    }
}