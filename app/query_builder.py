from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.sql import select, func, and_
from sqlalchemy.orm import Session
from sqlalchemy import Column, Table

from app.database import Customer
from app.translation_service import TermNotFoundError
from app.nlp_processor import QueryIntent

class QueryBuilder:
    # Map table names to their corresponding SQLAlchemy models
    TABLE_MAP = {
        'customer': Customer
    }
    
    # Map aggregation functions to SQLAlchemy functions
    AGG_MAP = {
        'COUNT': func.count,
        'SUM': func.sum,
        'AVG': func.avg,
        'MIN': func.min,
        'MAX': func.max
    }
    
    def __init__(self, dictionary, db_session: Session):
        self.dictionary = dictionary
        self.db = db_session
    
    def build_query(self, intent: QueryIntent):
        """Build a SQLAlchemy query from the query intent"""
        print(f"\n=== Building Query ===")
        print(f"Intent: {intent}")
        
        try:
            # Determine target entity (support legacy and dataclass shapes)
            target_entity = getattr(intent, 'target_entity', None)
            if not target_entity:
                if hasattr(intent, 'entities') and intent.entities:
                    target_entity = intent.entities[0]
                else:
                    target_entity = "לקוחות"
            print(f"Resolving entity: {target_entity}")
            # Resolve the main entity (e.g., "לקוחות" -> Customer.id)
            entity_mapping = self.dictionary.resolve(target_entity)
            print(f"Resolved to: {entity_mapping}")
            
            model = self.TABLE_MAP[entity_mapping.table]
            print(f"Using model: {model.__name__}")
            
            # Get the column to select/aggregate
            target_column = getattr(model, entity_mapping.field)
            print(f"Target column: {target_column}")

            # Detect display mode from intent metadata
            metadata = getattr(intent, 'metadata', {}) if intent is not None else {}
            display_fields = metadata.get('display_fields', None)

            if display_fields is not None:
                # Display mode: ignore aggregations, build a DISTINCT projection
                select_columns = []
                if isinstance(display_fields, list) and len(display_fields) > 0:
                    for term in display_fields:
                        try:
                            m = self.dictionary.resolve(term)
                            if m.table == entity_mapping.table:
                                col = getattr(model, m.field)
                                select_columns.append(col)
                        except TermNotFoundError:
                            continue
                # If no explicit display fields or none resolved, choose sensible defaults per entity
                if not select_columns:
                    # Defaults for customers
                    default_cols = []
                    for attr in ('id', 'name', 'city', 'created_at'):
                        if hasattr(model, attr):
                            default_cols.append(getattr(model, attr))
                    select_columns = default_cols or [target_column]
                print(f"Display mode active. Selecting columns: {select_columns}")
                # We'll build the SELECT after processing filters and potential ordering
                display_mode = True
            else:
                # Apply aggregation if needed (support legacy string or dataclass Aggregation)
                agg_name = getattr(intent, 'aggregation', None)
                if not agg_name and hasattr(intent, 'aggregations') and intent.aggregations:
                    first_agg = intent.aggregations[0]
                    try:
                        agg_name = first_agg.operation.value if hasattr(first_agg.operation, 'value') else str(first_agg.operation)
                    except Exception:
                        agg_name = None
                if agg_name:
                    agg_func = self.AGG_MAP.get(agg_name, func.count)
                    select_columns = [agg_func(target_column).label('result')]
                else:
                    select_columns = [target_column]
                display_mode = False
            
            # Apply filters (we'll attach to the query after building SELECT)
            filters = []
            print(f"Processing filters: {getattr(intent, 'filters', None)}")
            # Normalize filters to iterable of (field_name, value, operator)
            user_filters = getattr(intent, 'filters', None)
            if isinstance(user_filters, dict):
                items_iter = [(k, v, None) for k, v in user_filters.items()]
            elif isinstance(user_filters, list):
                items_iter = []
                for f in user_filters:
                    fname = getattr(f, 'field', None)
                    fval = getattr(f, 'value', None)
                    fop = getattr(f, 'operator', None)
                    if fname is not None:
                        items_iter.append((fname, fval, fop))
            else:
                items_iter = []

            from datetime import datetime, date

            for field_name, value, operator in items_iter:
                try:
                    print(f"\nProcessing filter: {field_name} = {value}")
                    field_mapping = self.dictionary.resolve(field_name)
                    print(f"Resolved field: {field_mapping}")
                    
                    if field_mapping.table == entity_mapping.table:
                        column = getattr(model, field_mapping.field)
                        print(f"Using column: {column}")
                        
                        # Special handling for location fields
                        if field_name in ["עיר", "ערים", "יישוב"]:
                            # Get all existing cities from the database
                            existing_cities = [row[0] for row in self.db.query(model.city).distinct().all()]
                            
                            # Try different matching strategies
                            matched_cities = []
                            
                            # 1. Exact match
                            if value in existing_cities:
                                matched_cities.append(value)
                            
                            # 2. Case-insensitive match and handle Hebrew encoding
                            if isinstance(value, str):
                                lower_value = value.lower().strip()
                                matched_cities.extend([city for city in existing_cities 
                                                    if city and city.lower().strip() == lower_value])
                            
                            # 3. Partial match (contains) with normalization
                            if not matched_cities and isinstance(value, str):
                                matched_cities.extend([city for city in existing_cities 
                                                    if city and value.strip() in city.strip()])
                            
                            # 4. Common spelling variations
                            if not matched_cities and isinstance(value, str):
                                variations = [
                                    value.replace("עלית", "עילית"),
                                    value.replace("עילית", "עלית"),
                                    value.replace(" ", "-"),
                                    value.replace("-", " ")
                                ]
                                matched_cities.extend([city for city in existing_cities 
                                                     if city and any(var in city for var in variations)])
                            
                            # Remove duplicates while preserving order
                            seen = set()
                            matched_cities = [city for city in matched_cities 
                                           if city and not (city in seen or seen.add(city))]
                            
                            print(f"Matching cities for '{value}': {matched_cities}")
                            
                            if matched_cities:
                                filters.append(column.in_(matched_cities))
                            else:
                                print(f"No matching cities found for: {value}")
                                print(f"Available cities: {existing_cities}")
                                # Still try with the original value in case of partial matches
                                if isinstance(value, str):
                                    filters.append(column.like(f"%{value}%"))
                        elif field_mapping.field == 'created_at':
                            # In display mode without explicit date, skip adding date filters entirely
                            has_explicit_date = False
                            try:
                                has_explicit_date = bool(getattr(intent, 'metadata', {}).get('has_explicit_date'))
                            except Exception:
                                has_explicit_date = False
                            if display_fields is not None and not has_explicit_date:
                                continue
                            # Handle date filters with proper Python date objects
                            def to_date(val):
                                if isinstance(val, date):
                                    return val
                                if isinstance(val, str) and val:
                                    try:
                                        return datetime.strptime(val[:10], '%Y-%m-%d').date()
                                    except ValueError:
                                        return None
                                return None

                            if operator and hasattr(operator, 'value') and operator.value == 'BETWEEN' and isinstance(value, (tuple, list)):
                                start, end = value[0], value[1]
                                d_start = to_date(start)
                                d_end = to_date(end)
                                if d_start and d_end:
                                    filters.append(column.between(d_start, d_end))
                                elif d_start and not d_end:
                                    filters.append(column >= d_start)
                                elif d_end and not d_start:
                                    filters.append(column <= d_end)
                                # If neither is valid, skip adding a filter
                            else:
                                d_val = to_date(value)
                                if d_val:
                                    filters.append(column == d_val)
                        else:
                            # Skip empty/None values to avoid invalid filters like id = NULL
                            if value not in (None, '') and value != {} and value != []:
                                filters.append(column == value)
                except TermNotFoundError as e:
                    print(f"Warning: Field '{field_name}' not found in dictionary")
                    print(f"Error details: {str(e)}")
                    print(f"Available terms: {list(self.dictionary._by_canonical.keys())}")
                except Exception as e:
                    print(f"Error processing filter {field_name}: {str(e)}")
                    raise
            
            # Before building SELECT, if we have aggregations and group-by, ensure grouped columns are included
            if display_fields is None and (hasattr(intent, 'aggregations') and intent.aggregations):
                gb = getattr(intent, 'group_by', None)
                if gb:
                    gb_fields = gb if isinstance(gb, list) else [gb]
                    for gb_field in gb_fields:
                        try:
                            group_mapping = self.dictionary.resolve(gb_field)
                            if group_mapping.table == entity_mapping.table:
                                group_column = getattr(model, group_mapping.field)
                                if group_column not in select_columns:
                                    select_columns.append(group_column)
                        except TermNotFoundError:
                            continue

            # Build SELECT now (after we might add GROUP BY columns to select_columns below)
            if display_fields is not None:
                query = select(*select_columns).distinct()
            else:
                query = select(*select_columns)
            # Attach filters
            if filters:
                query = query.where(and_(*filters))
            
            # Apply GROUP BY if needed (skip in display mode)
            if display_fields is None:
                gb = getattr(intent, 'group_by', None)
                if gb:
                    gb_fields = gb if isinstance(gb, list) else [gb]
                    for gb_field in gb_fields:
                        try:
                            group_mapping = self.dictionary.resolve(gb_field)
                            if group_mapping.table == entity_mapping.table:
                                group_column = getattr(model, group_mapping.field)
                                # Add grouped column to SELECT if missing
                                if group_column not in select_columns:
                                    select_columns.append(group_column)
                                # Rebuild SELECT to include the new column
                                query = select(*select_columns)
                                # Re-apply filters after rebuilding SELECT
                                if filters:
                                    query = query.where(and_(*filters))
                                # Finally, add GROUP BY
                                query = query.group_by(group_column)
                        except TermNotFoundError:
                            continue
            
            # Apply ORDER BY if needed
            ob = getattr(intent, 'order_by', None)
            if ob:
                if isinstance(ob, list) and ob:
                    order_column, direction = ob[0]
                elif isinstance(ob, tuple):
                    order_column, direction = ob
                else:
                    order_column, direction = None, None
                if order_column:
                    try:
                        order_mapping = self.dictionary.resolve(order_column)
                        if order_mapping.table == entity_mapping.table:
                            order_column = getattr(model, order_mapping.field)
                            if hasattr(direction, 'value'):
                                direction = direction.value
                            if isinstance(direction, str) and direction.upper() == 'DESC':
                                order_column = order_column.desc()
                            query = query.order_by(order_column)
                    except TermNotFoundError:
                        # Fallback: if we have an aggregation labeled as 'result', order by it
                        if select_columns:
                            agg_col = select_columns[0]
                            # Only apply if this is an aggregate/labeled column
                            try:
                                if hasattr(direction, 'value'):
                                    direction = direction.value
                                if isinstance(direction, str) and direction.upper() == 'DESC':
                                    query = query.order_by(agg_col.desc())
                                else:
                                    query = query.order_by(agg_col.asc())
                            except Exception:
                                pass
            
            # Apply LIMIT if needed
            if intent.limit:
                query = query.limit(intent.limit)
            
            return query
            
        except Exception as e:
            raise ValueError(f"Error building query: {str(e)}")
    
    def execute_query(self, query, intent: QueryIntent = None, format_as_text: bool = True):
        """Execute the query and format the results"""
        try:
            result = self.db.execute(query).fetchall()
            
            if not result or (len(result) == 1 and result[0][0] is None):
                # Extract city from either dict-style or list-style filters
                city = None
                if intent is not None:
                    filters_obj = getattr(intent, 'filters', None)
                    if isinstance(filters_obj, dict) and 'עיר' in filters_obj:
                        city = filters_obj['עיר']
                    elif isinstance(filters_obj, list):
                        for f in filters_obj:
                            if getattr(f, 'field', None) in ['עיר', 'ערים', 'יישוב']:
                                city = getattr(f, 'value', None)
                                break
                if city is not None:
                    return {
                        "answer": f"לא נמצאו תוצאות עבור העיר '{city}'. ייתכן שהעיר אינה קיימת במערכת או שאין נתונים זמינים.",
                        "sql": str(query),
                        "error": None
                    }
                return {
                    "answer": "לא נמצאו תוצאות התואמות את השאילתה.",
                    "sql": str(query),
                    "error": None
                }
            
            # Format the response based on the query type (success path)
            if format_as_text:
                if len(result[0]) == 1:  # Single column result (e.g., count, sum)
                    value = result[0][0]
                    # Determine aggregation (legacy string or dataclass Aggregation)
                    agg_name = None
                    if intent is not None:
                        agg_name = getattr(intent, 'aggregation', None)
                        if not agg_name and hasattr(intent, 'aggregations') and intent.aggregations:
                            first_agg = intent.aggregations[0]
                            try:
                                agg_name = first_agg.operation.value if hasattr(first_agg.operation, 'value') else str(first_agg.operation)
                            except Exception:
                                agg_name = None
                    # Determine entity name
                    entity = "פריטים"
                    if intent is not None:
                        te = getattr(intent, 'target_entity', None)
                        if not te and hasattr(intent, 'entities') and intent.entities:
                            te = intent.entities[0]
                        entity = te or entity
                    # Determine location text
                    location_txt = ""
                    if intent is not None:
                        filters_obj = getattr(intent, 'filters', None)
                        city = None
                        if isinstance(filters_obj, dict) and 'עיר' in filters_obj:
                            city = filters_obj['עיר']
                        elif isinstance(filters_obj, list):
                            for f in filters_obj:
                                if getattr(f, 'field', None) in ['עיר', 'ערים', 'יישוב']:
                                    city = getattr(f, 'value', None)
                                    break
                        if city:
                            location_txt = f" ב{city}"
                    if isinstance(agg_name, str) and agg_name.upper() == 'COUNT':
                        answer = f"נמצאו {value} {entity}{location_txt} במערכת"
                    else:
                        answer = f"תוצאה: {value}"
                else:  # Multiple columns
                    answer = "\n".join(", ".join(str(val) for val in row) for row in result)
                
                return {
                    "answer": answer,
                    "sql": str(query),
                    "error": None
                }
            
            # Fallback: return raw result if not formatting as text
            return result
            
        except Exception as e:
            error_msg = str(e).lower()
            if "no such column" in error_msg:
                return {
                    "answer": "אירעה שגיאה בעיבוד השאלה. ייתכן שהמידע המבוקש אינו זמין במערכת.",
                    "sql": str(query),
                    "error": str(e)
                }
            return {
                "answer": f"אירעה שגיאה בעיבוד התשובה: {str(e)}",
                "sql": str(query),
                "error": str(e)
            }
