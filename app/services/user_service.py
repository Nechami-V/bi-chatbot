"""
External users database (SQL Server or other) manager for authentication.

Aligns with the insert script schema:
  FirstName, LastName, PhoneNumber, EmailAddress, PasswordHash, IsManager, RoleGroup

Provides methods to fetch/authenticate users and returns hydrated app.models.user.User
instances (detached) so the rest of the app stays unchanged.
"""

from sqlalchemy import create_engine, text
from typing import List, Optional, Dict, Tuple

from app.models.user import User
from app.simple_config import config


class UserDatabase:
    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or config.USER_DATABASE_URL
        self.engine = create_engine(self.db_url, pool_pre_ping=True, pool_recycle=3600)

    def _hydrate_user_from_row(self, row) -> User:
        """Map external schema row to internal User DTO."""
        u = User()
        # Assuming row order per resolved mapping below
        u.id = row[0]
        u.first_name = row[1]
        u.last_name = row[2]
        u.phone = row[3]
        u.email = row[4]
        u.password = row[5]
        u.is_manager = bool(row[6]) if row[6] is not None else False
        u.permission_group = row[7] or "user"
        return u

    def _detect_table_schema(self, conn) -> Tuple[str, Dict[str, str]]:
        """Detect users table schema and column names.

        Returns (table_qualifier, colmap) where table_qualifier includes schema if available
        (e.g., [dbo].[users]) for MSSQL, and colmap maps logical names to actual column names.
        """
        dialect = self.engine.dialect.name

        # Get schema of 'users' table
        table_schema = None
        try:
            rs = conn.execute(text(
                "SELECT TOP 1 TABLE_SCHEMA FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'users'"
                if dialect == "mssql" else
                "SELECT TABLE_SCHEMA FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'users' LIMIT 1"
            ))
            row = rs.fetchone()
            if row and row[0]:
                table_schema = row[0]
        except Exception:
            table_schema = None

        # Fetch available columns
        cols: List[str] = []
        try:
            rs = conn.execute(text(
                "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'users'"
            ))
            cols = [r[0] for r in rs.fetchall()]
        except Exception:
            cols = []

        # Candidate name sets
        candidates = {
            'id': [
                'Id', 'ID', 'UserId', 'UserID', 'user_id', 'id', 'ID_USER', 'User_Id'
            ],
            'first_name': [
                'FirstName', 'first_name', 'First_Name', 'FName', 'fname', 'First'
            ],
            'last_name': [
                'LastName', 'last_name', 'Last_Name', 'LName', 'lname', 'Last'
            ],
            'phone': [
                'PhoneNumber', 'Phone', 'phone_number', 'phone', 'Mobile', 'MobilePhone'
            ],
            'email': [
                'EmailAddress', 'Email', 'email', 'email_address', 'E_mail'
            ],
            'password': [
                'PasswordHash', 'password_hash', 'HashedPassword', 'Password', 'pwdHash'
            ],
            'is_manager': [
                'IsManager', 'is_manager', 'Manager', 'Is_Manager', 'IsAdmin'
            ],
            'permission_group': [
                'RoleGroup', 'PermissionGroup', 'permission_group', 'Role', 'GroupName'
            ],
        }

        def pick(name_list: List[str]) -> Optional[str]:
            for n in name_list:
                if n in cols:
                    return n
            return None

        colmap: Dict[str, Optional[str]] = {k: pick(v) for k, v in candidates.items()}

        # Required: id, email, password. Try fallbacks if not found at all
        if not colmap['id']:
            # If no id, attempt ROW_NUMBER as surrogate is unsafe for auth; leave None
            pass
        if not colmap['email'] or not colmap['password']:
            # Without these, auth can't proceed; keep None, callers should handle
            pass

        # Qualify table
        if dialect == "mssql":
            if table_schema:
                table_qual = f"[{table_schema}].[users]"
            else:
                table_qual = "[users]"
        else:
            if table_schema:
                table_qual = f"{table_schema}.users"
            else:
                table_qual = "users"

        # Quote column names for MSSQL with []
        if dialect == "mssql":
            quoted = {k: (f"[{v}]" if v else None) for k, v in colmap.items()}
        else:
            # Leave unquoted for portability; assumes simple identifiers
            quoted = colmap  # type: ignore

        return table_qual, quoted  # type: ignore

    def get_user_by_email(self, email: str) -> Optional[User]:
        with self.engine.connect() as conn:
            table_qual, cols = self._detect_table_schema(conn)
            if not cols.get('email') or not cols.get('password'):
                return None
            # Build select list in fixed order to match _hydrate_user_from_row
            select_list = [
                cols.get('id') or 'NULL',
                cols.get('first_name') or 'NULL',
                cols.get('last_name') or 'NULL',
                cols.get('phone') or 'NULL',
                cols['email'],
                cols['password'],
                cols.get('is_manager') or 'NULL',
                cols.get('permission_group') or "'user'",
            ]
            select_sql = ", ".join(select_list)
            where_email = cols['email']

            if self.engine.dialect.name == "mssql":
                sql = f"SELECT TOP 1 {select_sql} FROM {table_qual} WHERE {where_email} = :email"
            else:
                sql = f"SELECT {select_sql} FROM {table_qual} WHERE {where_email} = :email LIMIT 1"

            row = conn.execute(text(sql), {"email": email}).fetchone()
            if not row:
                return None
            return self._hydrate_user_from_row(row)

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        with self.engine.connect() as conn:
            table_qual, cols = self._detect_table_schema(conn)
            if not cols.get('id'):
                return None
            select_list = [
                cols['id'],
                cols.get('first_name') or 'NULL',
                cols.get('last_name') or 'NULL',
                cols.get('phone') or 'NULL',
                cols.get('email') or 'NULL',
                cols.get('password') or 'NULL',
                cols.get('is_manager') or 'NULL',
                cols.get('permission_group') or "'user'",
            ]
            select_sql = ", ".join(select_list)
            where_id = cols['id']

            if self.engine.dialect.name == "mssql":
                sql = f"SELECT TOP 1 {select_sql} FROM {table_qual} WHERE {where_id} = :id"
            else:
                sql = f"SELECT {select_sql} FROM {table_qual} WHERE {where_id} = :id LIMIT 1"

            row = conn.execute(text(sql), {"id": user_id}).fetchone()
            if not row:
                return None
            return self._hydrate_user_from_row(row)

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        user = self.get_user_by_email(email)
        if user and user.check_password(password):
            return user
        return None

    def get_all_users(self) -> List[User]:
        with self.engine.connect() as conn:
            table_qual, cols = self._detect_table_schema(conn)
            select_list = [
                cols.get('id') or 'NULL',
                cols.get('first_name') or 'NULL',
                cols.get('last_name') or 'NULL',
                cols.get('phone') or 'NULL',
                cols.get('email') or 'NULL',
                cols.get('password') or 'NULL',
                cols.get('is_manager') or 'NULL',
                cols.get('permission_group') or "'user'",
            ]
            select_sql = ", ".join(select_list)
            sql = f"SELECT {select_sql} FROM {table_qual}"
            rows = conn.execute(text(sql)).fetchall()
            return [self._hydrate_user_from_row(r) for r in rows]


# Global database instance
user_db = UserDatabase()
