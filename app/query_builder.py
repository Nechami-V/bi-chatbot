from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.sql import select, func, and_
from sqlalchemy.orm import Session
from sqlalchemy import Column, Table

from app.database import Customer
from app.services.translation_service import TermNotFoundError
from app.services.nlp_processor import QueryIntent

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
            # Default to customers if no target entity is specified
            if not intent.target_entity:
                intent.target_entity = "לקוחות"
                print(f"Using default target_entity: {intent.target_entity}")
            
            print(f"Resolving entity: {intent.target_entity}")
            # Resolve the main entity (e.g., "לקוחות" -> Customer.id)
            entity_mapping = self.dictionary.resolve(intent.target_entity)
            print(f"Resolved to: {entity_mapping}")
            
            model = self.TABLE_MAP[entity_mapping.table]
            print(f"Using model: {model.__name__}")
            
            # Get the column to select/aggregate
            target_column = getattr(model, entity_mapping.field)
            print(f"Target column: {target_column}")
            
            # Apply aggregation if needed
            if intent.aggregation:
                agg_func = self.AGG_MAP.get(intent.aggregation, func.count)
                select_columns = [agg_func(target_column).label('result')]
            else:
                select_columns = [target_column]
            
            # Start building the query
            query = select(*select_columns)
            
            # Apply filters
            filters = []
            print(f"Processing filters: {intent.filters}")
            
            for field_name, value in intent.filters.items():
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
                            lower_value = value.lower().strip()
                            matched_cities.extend([city for city in existing_cities 
                                                if city and city.lower().strip() == lower_value])
                            
                            # 3. Partial match (contains) with normalization
                            if not matched_cities:
                                matched_cities.extend([city for city in existing_cities 
                                                    if city and value.strip() in city.strip()])
                            
                            # 4. Common spelling variations
                            if not matched_cities:
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
                                filters.append(column.like(f"%{value}%"))
                        else:
                            filters.append(column == value)
                except TermNotFoundError as e:
                    print(f"Warning: Field '{field_name}' not found in dictionary")
                    print(f"Error details: {str(e)}")
                    print(f"Available terms: {list(self.dictionary._by_canonical.keys())}")
                except Exception as e:
                    print(f"Error processing filter {field_name}: {str(e)}")
                    raise
            
            if filters:
                query = query.where(and_(*filters))
            
            # Apply GROUP BY if needed
            if intent.group_by:
                try:
                    group_mapping = self.dictionary.resolve(intent.group_by)
                    if group_mapping.table == entity_mapping.table:
                        group_column = getattr(model, group_mapping.field)
                        query = query.group_by(group_column)
                        select_columns.append(group_column)
                except TermNotFoundError:
                    pass
            
            # Apply ORDER BY if needed
            if intent.order_by:
                order_column, direction = intent.order_by
                try:
                    order_mapping = self.dictionary.resolve(order_column)
                    if order_mapping.table == entity_mapping.table:
                        order_column = getattr(model, order_mapping.field)
                        if direction.upper() == 'DESC':
                            order_column = order_column.desc()
                        query = query.order_by(order_column)
                except TermNotFoundError:
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
                if intent and "עיר" in intent.filters:
                    city = intent.filters["עיר"]
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
            
            # Format the response based on the query type
            if format_as_text:
                if len(result[0]) == 1:  # Single column result (e.g., count, sum)
                    value = result[0][0]
                    if intent and intent.aggregation == "COUNT":
                        entity = intent.target_entity or "פריטים"
                        location = f"ב{intent.filters['עיר']} " if intent.filters and "עיר" in intent.filters else ""
                        answer = f"נמצאו {value} {entity} {location}במערכת"
                    else:
                        answer = f"תוצאה: {value}"
                else:  # Multiple columns
                    answer = "\n".join(", ".join(str(val) for val in row) for row in result)
                
                return {
                    "answer": answer,
                    "sql": str(query),
                    "error": None
                }
            
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
