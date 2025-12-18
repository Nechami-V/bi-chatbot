"""
SQL Validator for SQL Server (SSMS/T-SQL)
==========================================
This module validates that generated SQL queries use only SQL Server (T-SQL) syntax
and do NOT contain SQLite, MySQL, or PostgreSQL specific functions.

When invalid syntax is detected, it raises a ValidationError with:
1. The forbidden pattern that was found
2. The correct SQL Server equivalent
3. Example of proper usage
"""

import re
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class SQLValidationError(Exception):
    """Raised when SQL contains forbidden non-SQL Server syntax."""
    
    def __init__(self, message: str, forbidden_pattern: str, sql_server_equivalent: str):
        self.message = message
        self.forbidden_pattern = forbidden_pattern
        self.sql_server_equivalent = sql_server_equivalent
        super().__init__(self.message)


# Forbidden patterns with their SQL Server equivalents
FORBIDDEN_PATTERNS = [
    # ============================================================
    # SQLite FORBIDDEN FUNCTIONS
    # ============================================================
    {
        "pattern": r"strftime\s*\(\s*['\"]%Y['\"]",
        "name": "SQLite strftime('%Y', ...)",
        "sql_server": "YEAR(column_name)",
        "example": "YEAR(order_date) instead of strftime('%Y', order_date)",
        "database": "SQLite"
    },
    {
        "pattern": r"strftime\s*\(\s*['\"]%m['\"]",
        "name": "SQLite strftime('%m', ...)",
        "sql_server": "MONTH(column_name)",
        "example": "MONTH(order_date) instead of strftime('%m', order_date)",
        "database": "SQLite"
    },
    {
        "pattern": r"strftime\s*\(\s*['\"]%d['\"]",
        "name": "SQLite strftime('%d', ...)",
        "sql_server": "DAY(column_name)",
        "example": "DAY(order_date) instead of strftime('%d', order_date)",
        "database": "SQLite"
    },
    {
        "pattern": r"strftime\s*\(\s*['\"]%W['\"]",
        "name": "SQLite strftime('%W', ...)",
        "sql_server": "DATEPART(week, column_name)",
        "example": "DATEPART(week, order_date) instead of strftime('%W', order_date)",
        "database": "SQLite"
    },
    {
        "pattern": r"strftime\s*\(",
        "name": "SQLite strftime()",
        "sql_server": "Use YEAR(), MONTH(), DAY(), DATEPART(), or FORMAT()",
        "example": "YEAR(order_date) or FORMAT(order_date, 'yyyy-MM-dd')",
        "database": "SQLite"
    },
    {
        "pattern": r"\bdate\s*\(\s*['\"]now['\"]",
        "name": "SQLite date('now')",
        "sql_server": "CAST(GETDATE() AS DATE)",
        "example": "CAST(GETDATE() AS DATE) instead of date('now')",
        "database": "SQLite"
    },
    {
        "pattern": r"\bdatetime\s*\(\s*['\"]now['\"]",
        "name": "SQLite datetime('now')",
        "sql_server": "GETDATE()",
        "example": "GETDATE() instead of datetime('now')",
        "database": "SQLite"
    },
    
    # ============================================================
    # MySQL FORBIDDEN FUNCTIONS
    # ============================================================
    {
        "pattern": r"\bCURDATE\s*\(\s*\)",
        "name": "MySQL CURDATE()",
        "sql_server": "CAST(GETDATE() AS DATE)",
        "example": "CAST(GETDATE() AS DATE) instead of CURDATE()",
        "database": "MySQL"
    },
    {
        "pattern": r"\bCURRENT_DATE\s*\(\s*\)",
        "name": "MySQL CURRENT_DATE()",
        "sql_server": "CAST(GETDATE() AS DATE)",
        "example": "CAST(GETDATE() AS DATE) instead of CURRENT_DATE()",
        "database": "MySQL"
    },
    {
        "pattern": r"\bNOW\s*\(\s*\)",
        "name": "MySQL NOW()",
        "sql_server": "GETDATE()",
        "example": "GETDATE() instead of NOW()",
        "database": "MySQL"
    },
    {
        "pattern": r"\bDATE_SUB\s*\(",
        "name": "MySQL DATE_SUB()",
        "sql_server": "DATEADD()",
        "example": "DATEADD(day, -7, GETDATE()) instead of DATE_SUB(CURDATE(), INTERVAL 7 DAY)",
        "database": "MySQL"
    },
    {
        "pattern": r"\bDATE_ADD\s*\(",
        "name": "MySQL DATE_ADD()",
        "sql_server": "DATEADD()",
        "example": "DATEADD(day, 7, GETDATE()) instead of DATE_ADD(CURDATE(), INTERVAL 7 DAY)",
        "database": "MySQL"
    },
    {
        "pattern": r"\bDATE\s*\(\s*NOW\s*\(\s*\)\s*\)",
        "name": "MySQL DATE(NOW())",
        "sql_server": "CAST(GETDATE() AS DATE)",
        "example": "CAST(GETDATE() AS DATE) instead of DATE(NOW())",
        "database": "MySQL"
    },
    {
        "pattern": r"\bINTERVAL\s+\d+\s+(DAY|WEEK|MONTH|YEAR|HOUR|MINUTE|SECOND)",
        "name": "MySQL INTERVAL syntax",
        "sql_server": "DATEADD()",
        "example": "DATEADD(day, -7, GETDATE()) instead of CURDATE() - INTERVAL 7 DAY",
        "database": "MySQL"
    },
    
    # ============================================================
    # PostgreSQL FORBIDDEN FUNCTIONS
    # ============================================================
    {
        "pattern": r"\bDATE_TRUNC\s*\(",
        "name": "PostgreSQL DATE_TRUNC()",
        "sql_server": "DATEADD() with DATEDIFF()",
        "example": "DATEADD(month, DATEDIFF(month, 0, order_date), 0) for start of month",
        "database": "PostgreSQL"
    },
    {
        "pattern": r"\bCURRENT_DATE\b(?!\s*\()",
        "name": "PostgreSQL CURRENT_DATE",
        "sql_server": "CAST(GETDATE() AS DATE)",
        "example": "CAST(GETDATE() AS DATE) instead of CURRENT_DATE",
        "database": "PostgreSQL"
    },
    {
        "pattern": r"\bCURRENT_TIMESTAMP\b(?!\s*\()",
        "name": "PostgreSQL CURRENT_TIMESTAMP",
        "sql_server": "GETDATE()",
        "example": "GETDATE() instead of CURRENT_TIMESTAMP",
        "database": "PostgreSQL"
    },
    {
        "pattern": r"INTERVAL\s+['\"]",
        "name": "PostgreSQL INTERVAL with quotes",
        "sql_server": "DATEADD()",
        "example": "DATEADD(day, -7, GETDATE()) instead of CURRENT_DATE - INTERVAL '7 days'",
        "database": "PostgreSQL"
    },
    
    # ============================================================
    # LIMIT (not SQL Server)
    # ============================================================
    {
        "pattern": r"\bLIMIT\s+\d+",
        "name": "LIMIT clause (SQLite/MySQL/PostgreSQL)",
        "sql_server": "TOP N or OFFSET/FETCH",
        "example": "SELECT TOP 10 * FROM ... or SELECT * FROM ... ORDER BY ... OFFSET 0 ROWS FETCH NEXT 10 ROWS ONLY",
        "database": "SQLite/MySQL/PostgreSQL"
    },
]


def validate_sql(sql: str, strict: bool = True) -> Tuple[bool, Optional[SQLValidationError]]:
    """
    Validate that SQL uses only SQL Server (T-SQL) syntax.
    
    Args:
        sql: The SQL query to validate
        strict: If True, raise exception on first error. If False, return error info.
        
    Returns:
        Tuple of (is_valid, error_or_none)
        
    Raises:
        SQLValidationError: If strict=True and forbidden syntax is found
    """
    if not sql or not sql.strip():
        return True, None
    
    for pattern_info in FORBIDDEN_PATTERNS:
        pattern = pattern_info["pattern"]
        
        # Search case-insensitive
        match = re.search(pattern, sql, re.IGNORECASE)
        
        if match:
            error_msg = (
                f"❌ FORBIDDEN {pattern_info['database']} SYNTAX DETECTED!\n\n"
                f"Found: {pattern_info['name']}\n"
                f"Matched text: {match.group(0)}\n\n"
                f"✅ Use SQL Server instead:\n"
                f"{pattern_info['sql_server']}\n\n"
                f"Example:\n"
                f"{pattern_info['example']}\n\n"
                f"This system ONLY supports SQL Server (SSMS/T-SQL) syntax.\n"
                f"SQLite, MySQL, and PostgreSQL functions are NOT allowed."
            )
            
            error = SQLValidationError(
                message=error_msg,
                forbidden_pattern=pattern_info['name'],
                sql_server_equivalent=pattern_info['sql_server']
            )
            
            if strict:
                logger.error(f"SQL Validation Failed: {error_msg}")
                logger.error(f"Full SQL:\n{sql}")
                raise error
            else:
                return False, error
    
    return True, None


def get_validation_summary() -> str:
    """
    Get a summary of all validation rules.
    Used for documentation and debugging.
    """
    summary = "SQL Server Validation Rules\n"
    summary += "=" * 50 + "\n\n"
    
    databases = {}
    for pattern in FORBIDDEN_PATTERNS:
        db = pattern['database']
        if db not in databases:
            databases[db] = []
        databases[db].append(pattern)
    
    for db_name, patterns in databases.items():
        summary += f"\n{db_name} Forbidden Patterns:\n"
        summary += "-" * 30 + "\n"
        for p in patterns:
            summary += f"  ❌ {p['name']}\n"
            summary += f"     → {p['sql_server']}\n"
            summary += f"     Example: {p['example']}\n\n"
    
    return summary


if __name__ == "__main__":
    # Test the validator
    print(get_validation_summary())
    
    # Test cases
    test_cases = [
        ("SELECT YEAR(order_date) FROM orders", True, "Valid SQL Server"),
        ("SELECT strftime('%Y', order_date) FROM orders", False, "SQLite strftime"),
        ("SELECT * FROM orders WHERE date > CURDATE()", False, "MySQL CURDATE"),
        ("SELECT DATE_TRUNC('month', order_date) FROM orders", False, "PostgreSQL DATE_TRUNC"),
        ("SELECT TOP 10 * FROM orders", True, "Valid TOP"),
        ("SELECT * FROM orders LIMIT 10", False, "Invalid LIMIT"),
    ]
    
    print("\n" + "=" * 50)
    print("RUNNING TEST CASES")
    print("=" * 50 + "\n")
    
    for sql, should_pass, description in test_cases:
        print(f"Test: {description}")
        print(f"SQL: {sql}")
        
        try:
            is_valid, error = validate_sql(sql, strict=False)
            
            if should_pass and is_valid:
                print("✅ PASS (as expected)\n")
            elif not should_pass and not is_valid:
                print(f"✅ PASS (correctly rejected)\n")
            else:
                print(f"❌ FAIL (expected {'valid' if should_pass else 'invalid'}, got {'valid' if is_valid else 'invalid'})\n")
                
        except Exception as e:
            print(f"❌ ERROR: {e}\n")
