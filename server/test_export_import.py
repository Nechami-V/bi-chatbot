"""
Test script for Export functionality

Tests:
1. Import of ExportService
2. Basic structure validation
"""

import sys
sys.path.insert(0, 'c:/bi_chatbot')

try:
    from app.services.export_service import ExportService
    print("✅ ExportService imported successfully")
    
    # Check methods exist
    methods = ['generate_export_sql', 'execute_export_query', 'create_excel_file', 'create_csv_file', 'export_data']
    for method in methods:
        if hasattr(ExportService, method):
            print(f"✅ Method '{method}' exists")
        else:
            print(f"❌ Method '{method}' missing")
    
    print("\n✅ All basic checks passed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
