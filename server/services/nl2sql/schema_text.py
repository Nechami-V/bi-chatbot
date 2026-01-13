SCHEMA_TEXT = """
Database (SQL Server):

Tables:
- dbo.W_Orders(id, time, amount, parentId, itemId)
- dbo.parents(id, name, week)
- dbo.Dates(date_en, CurrentWeek, week_gregorian)

Notes:
- Use dbo schema.
- time is a datetime.
"""
