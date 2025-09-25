from typing import Any, List
from sqlalchemy.sql import select, func, and_
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.client import Client
from app.models.item import Item
from app.models.order import Order
from app.models.sale import Sale
from app.services.translation_service import TermNotFoundError
from app.services.nlp_processor import (
    QueryIntent,
    FilterCondition,
    ComparisonOperator,
    SortOrder,
)

class QueryBuilder:
    # Map table names to their corresponding SQLAlchemy models
    TABLE_MAP = {
        'customer': Customer,
        'ClientsBot2025': Client,
        'ItemsBot2025': Item,
        'OrdersBot2025': Order,
        'SalesBot2025': Sale
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
        """Build a SQLAlchemy query from the query intent (supports dataclass and legacy styles)"""
        print("\n=== Building Query ===")
        print(f"Intent: {intent}")

        try:
            # Resolve target entity
            target_entity = None
            if hasattr(intent, 'entities') and getattr(intent, 'entities'):
                target_entity = intent.entities[0]
            elif hasattr(intent, 'target_entity') and getattr(intent, 'target_entity'):
                target_entity = intent.target_entity
            else:
                target_entity = "לקוחות"
                print(f"Using default target_entity: {target_entity}")

            print(f"Resolving entity: {target_entity}")
            entity_mapping = self.dictionary.resolve(target_entity)
            print(f"Resolved to: {entity_mapping}")

            model = self.TABLE_MAP[entity_mapping.table]
            print(f"Using model: {model.__name__}")

            target_column = getattr(model, entity_mapping.field)
            print(f"Target column: {target_column}")

            # Determine aggregation function
            agg_func = None
            if hasattr(intent, 'aggregations') and getattr(intent, 'aggregations'):
                first_agg = intent.aggregations[0]
                agg_val = first_agg.operation.value if hasattr(first_agg, 'operation') and hasattr(first_agg.operation, 'value') else str(getattr(first_agg, 'operation', 'COUNT'))
                agg_func = self.AGG_MAP.get(str(agg_val), func.count)
            elif hasattr(intent, 'aggregation') and getattr(intent, 'aggregation'):
                agg_func = self.AGG_MAP.get(str(intent.aggregation), func.count)
            else:
                agg_func = func.count

            select_columns = [agg_func(target_column).label('result')]
            
            # Add GROUP BY columns to SELECT if they exist
            group_by_columns = []
            if hasattr(intent, 'group_by') and getattr(intent, 'group_by'):
                group_by_items = intent.group_by if isinstance(intent.group_by, list) else [intent.group_by]
                for gb in group_by_items:
                    try:
                        group_mapping = self.dictionary.resolve(gb)
                        if group_mapping.table == entity_mapping.table:
                            group_column = getattr(model, group_mapping.field)
                            select_columns.append(group_column)
                            group_by_columns.append(group_column)
                    except TermNotFoundError:
                        pass
            
            query = select(*select_columns)

            # Build filters
            filters_sql = []
            filters_obj = getattr(intent, 'filters', None)
            print(f"Processing filters: {filters_obj}")

            if isinstance(filters_obj, dict):
                for field_name, value in filters_obj.items():
                    try:
                        field_mapping = self.dictionary.resolve(field_name)
                        if field_mapping.table == entity_mapping.table:
                            column = getattr(model, field_mapping.field)
                            if field_name in ["עיר", "ערים", "יישוב"]:
                                filters_sql.append(self._build_city_filter(column, value, model))
                            else:
                                filters_sql.append(column == value)
                    except TermNotFoundError:
                        pass
            elif isinstance(filters_obj, list):
                for f in filters_obj:
                    if not isinstance(f, FilterCondition):
                        continue
                    try:
                        field_mapping = self.dictionary.resolve(f.field)
                        if field_mapping.table == entity_mapping.table:
                            column = getattr(model, field_mapping.field)
                            if f.field in ["עיר", "ערים", "יישוב"] and f.value is not None:
                                filters_sql.append(self._build_city_filter(column, f.value, model))
                            else:
                                op = f.operator
                                if op == ComparisonOperator.EQUALS:
                                    filters_sql.append(column == f.value)
                                elif op == ComparisonOperator.NOT_EQUALS:
                                    filters_sql.append(column != f.value)
                                elif op == ComparisonOperator.GREATER_OR_EQUAL:
                                    filters_sql.append(column >= f.value)
                                elif op == ComparisonOperator.GREATER_THAN:
                                    filters_sql.append(column > f.value)
                                elif op == ComparisonOperator.LESS_OR_EQUAL:
                                    filters_sql.append(column <= f.value)
                                elif op == ComparisonOperator.LESS_THAN:
                                    filters_sql.append(column < f.value)
                                elif op == ComparisonOperator.LIKE:
                                    filters_sql.append(column.ilike(f"%{f.value}%"))
                                elif op == ComparisonOperator.IN and isinstance(f.value, (list, tuple)):
                                    filters_sql.append(column.in_(list(f.value)))
                                else:
                                    filters_sql.append(column == f.value)
                    except TermNotFoundError:
                        pass

            if filters_sql:
                query = query.where(and_(*filters_sql))

            # GROUP BY (use columns we already calculated)
            for group_column in group_by_columns:
                query = query.group_by(group_column)

            # ORDER BY
            orders = getattr(intent, 'order_by', None)
            if orders:
                if not isinstance(orders, list):
                    orders = [orders]
                for order in orders:
                    try:
                        field, direction = order
                        order_mapping = self.dictionary.resolve(field)
                        if order_mapping.table == entity_mapping.table:
                            order_column = getattr(model, order_mapping.field)
                            dir_val = direction.value if isinstance(direction, SortOrder) else str(direction)
                            if dir_val.upper() == 'DESC':
                                order_column = order_column.desc()
                            query = query.order_by(order_column)
                    except (ValueError, TermNotFoundError):
                        pass

            # LIMIT
            if hasattr(intent, 'limit') and getattr(intent, 'limit'):
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
                    # Infer COUNT and entity/location from both styles
                    is_count = True
                    if intent is not None:
                        if hasattr(intent, 'aggregations') and getattr(intent, 'aggregations'):
                            agg = intent.aggregations[0]
                            agg_type = getattr(agg, 'operation', None)
                            agg_val = agg_type.value if hasattr(agg_type, 'value') else str(agg_type)
                            is_count = (str(agg_val).upper() == 'COUNT')
                        elif hasattr(intent, 'aggregation') and getattr(intent, 'aggregation'):
                            is_count = (str(intent.aggregation).upper() == 'COUNT')
                    entity = None
                    if intent is not None:
                        if hasattr(intent, 'entities') and getattr(intent, 'entities'):
                            entity = intent.entities[0]
                        elif hasattr(intent, 'target_entity') and getattr(intent, 'target_entity'):
                            entity = intent.target_entity
                    entity = entity or "פריטים"
                    # Location
                    location = ""
                    if intent is not None:
                        filt = getattr(intent, 'filters', None)
                        if isinstance(filt, dict) and "עיר" in filt:
                            location = f"ב{filt['עיר']} "
                        elif isinstance(filt, list):
                            for f in filt:
                                if isinstance(f, FilterCondition) and f.field == "עיר":
                                    location = f"ב{f.value} "
                                    break
                    if is_count:
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

    def _build_city_filter(self, column, value: Any, model) -> Any:
        """Build a robust city filter supporting fuzzy matches and LIKE as fallback."""
        # Get all existing cities from the database
        existing_cities = [row[0] for row in self.db.query(model.city).distinct().all()]

        matched_cities: List[str] = []

        if isinstance(value, (list, tuple)):
            candidates = list(value)
        else:
            candidates = [value]

        for v in candidates:
            if v in existing_cities:
                matched_cities.append(v)
            lower_v = str(v).lower().strip()
            matched_cities.extend([
                city for city in existing_cities
                if city and city.lower().strip() == lower_v
            ])
            matched_cities.extend([
                city for city in existing_cities
                if city and (str(city).startswith(str(v)) or str(v) in str(city))
            ])

        matched_cities = list(dict.fromkeys([c for c in matched_cities if c]))
        if matched_cities:
            return column.in_(matched_cities)
        return column.ilike(f"%{value}%")
