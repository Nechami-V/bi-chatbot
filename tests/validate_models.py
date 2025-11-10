"""
Validate multi-tenant models structure and relationships
"""
from sqlalchemy import inspect, create_engine
from sqlalchemy.orm import sessionmaker
from app.models import (
    Tenant, TenantUser, Session, UsageDaily, 
    SavedReport, ReportRun, Quota, ExternalIdentity
)
from app.db.database import Base

def validate_relationships():
    """Validate all model relationships are correctly defined"""
    print("=" * 60)
    print("בדיקת קשרים בין טבלאות")
    print("=" * 60)
    
    checks = []
    
    # Tenant relationships
    tenant_rels = {rel.key: rel.mapper.class_.__name__ for rel in inspect(Tenant).relationships}
    checks.append(("Tenant → users", tenant_rels.get("users") == "TenantUser"))
    checks.append(("Tenant → sessions", tenant_rels.get("sessions") == "Session"))
    checks.append(("Tenant → saved_reports", tenant_rels.get("saved_reports") == "SavedReport"))
    checks.append(("Tenant → report_runs", tenant_rels.get("report_runs") == "ReportRun"))
    checks.append(("Tenant → usage_records", tenant_rels.get("usage_records") == "UsageDaily"))
    checks.append(("Tenant → quota", tenant_rels.get("quota") == "Quota"))
    
    # TenantUser relationships
    user_rels = {rel.key: rel.mapper.class_.__name__ for rel in inspect(TenantUser).relationships}
    checks.append(("TenantUser → tenant", user_rels.get("tenant") == "Tenant"))
    checks.append(("TenantUser → sessions", user_rels.get("sessions") == "Session"))
    checks.append(("TenantUser → saved_reports", user_rels.get("saved_reports") == "SavedReport"))
    checks.append(("TenantUser → usage_records", user_rels.get("usage_records") == "UsageDaily"))
    checks.append(("TenantUser → external_identities", user_rels.get("external_identities") == "ExternalIdentity"))
    
    # Session relationships
    session_rels = {rel.key: rel.mapper.class_.__name__ for rel in inspect(Session).relationships}
    checks.append(("Session → tenant", session_rels.get("tenant") == "Tenant"))
    checks.append(("Session → user", session_rels.get("user") == "TenantUser"))
    
    # SavedReport relationships
    report_rels = {rel.key: rel.mapper.class_.__name__ for rel in inspect(SavedReport).relationships}
    checks.append(("SavedReport → tenant", report_rels.get("tenant") == "Tenant"))
    checks.append(("SavedReport → creator", report_rels.get("creator") == "TenantUser"))
    checks.append(("SavedReport → report_runs", report_rels.get("report_runs") == "ReportRun"))
    
    # ReportRun relationships
    run_rels = {rel.key: rel.mapper.class_.__name__ for rel in inspect(ReportRun).relationships}
    checks.append(("ReportRun → report", run_rels.get("report") == "SavedReport"))
    checks.append(("ReportRun → tenant", run_rels.get("tenant") == "Tenant"))
    checks.append(("ReportRun → executor", run_rels.get("executor") == "TenantUser"))
    
    # UsageDaily relationships
    usage_rels = {rel.key: rel.mapper.class_.__name__ for rel in inspect(UsageDaily).relationships}
    checks.append(("UsageDaily → tenant", usage_rels.get("tenant") == "Tenant"))
    checks.append(("UsageDaily → user", usage_rels.get("user") == "TenantUser"))
    
    # ExternalIdentity relationships
    ext_rels = {rel.key: rel.mapper.class_.__name__ for rel in inspect(ExternalIdentity).relationships}
    checks.append(("ExternalIdentity → user", ext_rels.get("user") == "TenantUser"))
    
    # Quota relationships
    quota_rels = {rel.key: rel.mapper.class_.__name__ for rel in inspect(Quota).relationships}
    checks.append(("Quota → tenant", quota_rels.get("tenant") == "Tenant"))
    
    # Print results
    passed = 0
    failed = 0
    for check_name, result in checks:
        status = "✓" if result else "✗"
        print(f"{status} {check_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"תוצאות: {passed} עבר, {failed} נכשל")
    print("=" * 60)
    
    return failed == 0


def validate_foreign_keys():
    """Validate all foreign keys point to correct tables"""
    print("\n" + "=" * 60)
    print("בדיקת Foreign Keys")
    print("=" * 60)
    
    checks = []
    
    # TenantUser FKs
    user_cols = {col.name: list(col.foreign_keys)[0].target_fullname if col.foreign_keys else None 
                 for col in inspect(TenantUser).columns}
    checks.append(("TenantUser.tenant_id → tenants.id", user_cols.get("tenant_id") == "tenants.id"))
    
    # Session FKs
    session_cols = {col.name: list(col.foreign_keys)[0].target_fullname if col.foreign_keys else None 
                    for col in inspect(Session).columns}
    checks.append(("Session.tenant_id → tenants.id", session_cols.get("tenant_id") == "tenants.id"))
    checks.append(("Session.user_id → tenant_users.id", session_cols.get("user_id") == "tenant_users.id"))
    
    # UsageDaily FKs
    usage_cols = {col.name: list(col.foreign_keys)[0].target_fullname if col.foreign_keys else None 
                  for col in inspect(UsageDaily).columns}
    checks.append(("UsageDaily.tenant_id → tenants.id", usage_cols.get("tenant_id") == "tenants.id"))
    checks.append(("UsageDaily.user_id → tenant_users.id", usage_cols.get("user_id") == "tenant_users.id"))
    
    # SavedReport FKs
    report_cols = {col.name: list(col.foreign_keys)[0].target_fullname if col.foreign_keys else None 
                   for col in inspect(SavedReport).columns}
    checks.append(("SavedReport.tenant_id → tenants.id", report_cols.get("tenant_id") == "tenants.id"))
    checks.append(("SavedReport.created_by → tenant_users.id", report_cols.get("created_by") == "tenant_users.id"))
    
    # ReportRun FKs
    run_cols = {col.name: list(col.foreign_keys)[0].target_fullname if col.foreign_keys else None 
                for col in inspect(ReportRun).columns}
    checks.append(("ReportRun.report_id → saved_reports.id", run_cols.get("report_id") == "saved_reports.id"))
    checks.append(("ReportRun.tenant_id → tenants.id", run_cols.get("tenant_id") == "tenants.id"))
    checks.append(("ReportRun.executed_by → tenant_users.id", run_cols.get("executed_by") == "tenant_users.id"))
    
    # ExternalIdentity FKs
    ext_cols = {col.name: list(col.foreign_keys)[0].target_fullname if col.foreign_keys else None 
                for col in inspect(ExternalIdentity).columns}
    checks.append(("ExternalIdentity.user_id → tenant_users.id", ext_cols.get("user_id") == "tenant_users.id"))
    
    # Quota FKs
    quota_cols = {col.name: list(col.foreign_keys)[0].target_fullname if col.foreign_keys else None 
                  for col in inspect(Quota).columns}
    checks.append(("Quota.tenant_id → tenants.id", quota_cols.get("tenant_id") == "tenants.id"))
    
    # Print results
    passed = 0
    failed = 0
    for check_name, result in checks:
        status = "✓" if result else "✗"
        print(f"{status} {check_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"תוצאות: {passed} עבר, {failed} נכשל")
    print("=" * 60)
    
    return failed == 0


def validate_cascade_deletes():
    """Validate CASCADE delete is configured correctly"""
    print("\n" + "=" * 60)
    print("בדיקת CASCADE Deletes")
    print("=" * 60)
    
    checks = []
    
    # TenantUser cascade from Tenant
    user_fks = [fk for col in inspect(TenantUser).columns for fk in col.foreign_keys if fk.column.table.name == "tenants"]
    checks.append(("TenantUser ON DELETE CASCADE", 
                  any(fk.ondelete == "CASCADE" for fk in user_fks)))
    
    # Session cascade from Tenant and TenantUser
    session_fks = [fk for col in inspect(Session).columns for fk in col.foreign_keys]
    checks.append(("Session.tenant_id ON DELETE CASCADE", 
                  any(fk.ondelete == "CASCADE" and fk.column.table.name == "tenants" for fk in session_fks)))
    checks.append(("Session.user_id ON DELETE CASCADE", 
                  any(fk.ondelete == "CASCADE" and fk.column.table.name == "tenant_users" for fk in session_fks)))
    
    # UsageDaily cascade
    usage_fks = [fk for col in inspect(UsageDaily).columns for fk in col.foreign_keys]
    checks.append(("UsageDaily.tenant_id ON DELETE CASCADE", 
                  any(fk.ondelete == "CASCADE" and fk.column.table.name == "tenants" for fk in usage_fks)))
    checks.append(("UsageDaily.user_id ON DELETE CASCADE", 
                  any(fk.ondelete == "CASCADE" and fk.column.table.name == "tenant_users" for fk in usage_fks)))
    
    # SavedReport cascade
    report_fks = [fk for col in inspect(SavedReport).columns for fk in col.foreign_keys]
    checks.append(("SavedReport.tenant_id ON DELETE CASCADE", 
                  any(fk.ondelete == "CASCADE" and fk.column.table.name == "tenants" for fk in report_fks)))
    
    # ReportRun cascade
    run_fks = [fk for col in inspect(ReportRun).columns for fk in col.foreign_keys]
    checks.append(("ReportRun.report_id ON DELETE CASCADE", 
                  any(fk.ondelete == "CASCADE" and fk.column.table.name == "saved_reports" for fk in run_fks)))
    
    # ExternalIdentity cascade
    ext_fks = [fk for col in inspect(ExternalIdentity).columns for fk in col.foreign_keys]
    checks.append(("ExternalIdentity.user_id ON DELETE CASCADE", 
                  any(fk.ondelete == "CASCADE" for fk in ext_fks)))
    
    # Print results
    passed = 0
    failed = 0
    for check_name, result in checks:
        status = "✓" if result else "✗"
        print(f"{status} {check_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"תוצאות: {passed} עבר, {failed} נכשל")
    print("=" * 60)
    
    return failed == 0


def validate_indexes():
    """Validate important indexes are defined"""
    print("\n" + "=" * 60)
    print("בדיקת Indexes")
    print("=" * 60)
    
    checks = []
    
    # TenantUser indexes
    user_indexes = {col.name: col.index or col.unique for col in inspect(TenantUser).columns}
    checks.append(("TenantUser.email indexed/unique", user_indexes.get("email")))
    checks.append(("TenantUser.tenant_id indexed", user_indexes.get("tenant_id")))
    
    # Session indexes
    session_indexes = {col.name: col.index for col in inspect(Session).columns}
    checks.append(("Session.session_id indexed", session_indexes.get("session_id")))
    checks.append(("Session.tenant_id indexed", session_indexes.get("tenant_id")))
    
    # SavedReport indexes
    report_indexes = {col.name: col.index for col in inspect(SavedReport).columns}
    checks.append(("SavedReport.tenant_id indexed", report_indexes.get("tenant_id")))
    
    # UsageDaily indexes
    usage_indexes = {col.name: col.index for col in inspect(UsageDaily).columns}
    checks.append(("UsageDaily.usage_date indexed", usage_indexes.get("usage_date")))
    checks.append(("UsageDaily.tenant_id indexed", usage_indexes.get("tenant_id")))
    
    # Print results
    passed = 0
    failed = 0
    for check_name, result in checks:
        status = "✓" if result else "✗"
        print(f"{status} {check_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"תוצאות: {passed} עבר, {failed} נכשל")
    print("=" * 60)
    
    return failed == 0


def print_schema_summary():
    """Print summary of all tables and their columns"""
    print("\n" + "=" * 60)
    print("סיכום סכמת הטבלאות")
    print("=" * 60)
    
    models = [
        ("tenants", Tenant),
        ("tenant_users", TenantUser),
        ("sessions", Session),
        ("usage_daily", UsageDaily),
        ("saved_reports", SavedReport),
        ("report_runs", ReportRun),
        ("quotas", Quota),
        ("external_identities", ExternalIdentity)
    ]
    
    for table_name, model in models:
        print(f"\n📊 {table_name}")
        print("-" * 60)
        
        # Columns
        for col in inspect(model).columns:
            fk = f" → {list(col.foreign_keys)[0].target_fullname}" if col.foreign_keys else ""
            nullable = "NULL" if col.nullable else "NOT NULL"
            pk = " 🔑" if col.primary_key else ""
            idx = " 📇" if col.index else ""
            unique = " 🔐" if col.unique else ""
            print(f"  • {col.name}: {col.type}{fk} ({nullable}){pk}{idx}{unique}")
        
        # Relationships
        rels = inspect(model).relationships
        if rels:
            print("  Relationships:")
            for rel in rels:
                print(f"    → {rel.key}: {rel.mapper.class_.__name__}")


if __name__ == "__main__":
    print("\n🔍 בדיקת תקינות המודלים של Multi-Tenant\n")
    
    all_passed = True
    
    # Run all validations
    all_passed &= validate_relationships()
    all_passed &= validate_foreign_keys()
    all_passed &= validate_cascade_deletes()
    all_passed &= validate_indexes()
    
    # Print schema summary
    print_schema_summary()
    
    # Final result
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ כל הבדיקות עברו בהצלחה!")
        print("המודלים מוכנים ליצירת Alembic migration")
    else:
        print("❌ יש בעיות שצריך לתקן לפני המיגרציה")
    print("=" * 60 + "\n")
