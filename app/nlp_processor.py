from typing import Dict, List, Optional, Tuple, Set, Any, Union
import re
import json
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum, auto
from collections import defaultdict
import numpy as np
from rapidfuzz import fuzz
from dateutil.relativedelta import relativedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import with error handling
try:
    from .translation_service import TranslationDictionary, TermNotFoundError
except ImportError:
    logger.warning("TranslationDictionary not found, using fallback")
    
    class TermNotFoundError(Exception):
        pass
        
    class TranslationDictionary:
        def __init__(self):
            self._by_canonical = {}
            self._alias_index = {}

# Enums for better type safety
class AggregationType(Enum):
    COUNT = "COUNT"
    SUM = "SUM"
    AVG = "AVG"
    MIN = "MIN"
    MAX = "MAX"
    COUNT_DISTINCT = "COUNT_DISTINCT"
    MEDIAN = "MEDIAN"
    STDDEV = "STDDEV"
    VARIANCE = "VARIANCE"

class TimeGranularity(Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"

class ComparisonOperator(Enum):
    EQUALS = "="
    NOT_EQUALS = "!="
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_OR_EQUAL = ">="
    LESS_OR_EQUAL = "<="
    BETWEEN = "BETWEEN"
    IN = "IN"
    LIKE = "LIKE"
    IS_NULL = "IS NULL"
    IS_NOT_NULL = "IS NOT NULL"

class SortOrder(Enum):
    ASC = "ASC"
    DESC = "DESC"

@dataclass
class TimeFrame:
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    granularity: Optional[TimeGranularity] = None
    is_relative: bool = False
    relative_value: int = 0
    relative_unit: str = "days"

@dataclass
class FilterCondition:
    field: str
    operator: ComparisonOperator
    value: Any
    value_type: str = "literal"  # literal, column, function
    
    def to_sql(self) -> str:
        if self.operator == ComparisonOperator.BETWEEN:
            return f"{self.field} BETWEEN {self.value[0]} AND {self.value[1]}"
        elif self.operator == ComparisonOperator.IN:
            values = ", ".join(str(v) for v in self.value)
            return f"{self.field} IN ({values})"
        else:
            return f"{self.field} {self.operator.value} {self.value}"

@dataclass
class Aggregation:
    field: str
    operation: AggregationType
    alias: Optional[str] = None
    
    def to_sql(self) -> str:
        sql = f"{self.operation.value}({self.field})"
        if self.alias:
            sql += f" AS {self.alias}"
        return sql

@dataclass
class QueryIntent:
    """Represents the structured intent of a BI query."""
    # Core elements
    entities: List[str] = field(default_factory=list)
    aggregations: List[Aggregation] = field(default_factory=list)
    filters: List[FilterCondition] = field(default_factory=list)
    time_dimension: Optional[str] = None
    time_frame: Optional[TimeFrame] = None
    
    # Grouping and ordering
    group_by: List[str] = field(default_factory=list)
    order_by: List[Tuple[str, SortOrder]] = field(default_factory=list)
    limit: Optional[int] = None
    
    # Context and metadata
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_filter(self, field: str, operator: Union[str, ComparisonOperator], value: Any):
        """Add a filter condition to the query."""
        if isinstance(operator, str):
            operator = ComparisonOperator(operator.upper())
        self.filters.append(FilterCondition(field, operator, value))
    
    def add_aggregation(self, field: str, operation: Union[str, AggregationType], alias: Optional[str] = None):
        """Add an aggregation to the query."""
        if isinstance(operation, str):
            operation = AggregationType(operation.upper())
        self.aggregations.append(Aggregation(field, operation, alias))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the intent to a dictionary for serialization."""
        return {
            "entities": self.entities,
            "aggregations": [{"field": a.field, "operation": a.operation.value, "alias": a.alias} 
                            for a in self.aggregations],
            "filters": [{"field": f.field, "operator": f.operator.value, "value": f.value}
                        for f in self.filters],
            "time_dimension": self.time_dimension,
            "group_by": self.group_by,
            "order_by": [(field, order.value) for field, order in self.order_by],
            "limit": self.limit,
            "context": self.context
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QueryIntent':
        """Create a QueryIntent from a dictionary."""
        intent = cls()
        intent.entities = data.get("entities", [])
        intent.aggregations = [
            Aggregation(
                field=a["field"],
                operation=AggregationType(a["operation"]),
                alias=a.get("alias")
            ) for a in data.get("aggregations", [])
        ]
        intent.filters = [
            FilterCondition(
                field=f["field"],
                operator=ComparisonOperator(f["operator"]),
                value=f["value"]
            ) for f in data.get("filters", [])
        ]
        intent.time_dimension = data.get("time_dimension")
        intent.group_by = data.get("group_by", [])
        intent.order_by = [
            (field, SortOrder(order)) for field, order in data.get("order_by", [])
        ]
        intent.limit = data.get("limit")
        intent.context = data.get("context", {})
        return intent
    
    def __repr__(self) -> str:
        parts = []
        
        # Add aggregations
        if self.aggregations:
            aggs = ", ".join(str(agg) for agg in self.aggregations)
            parts.append(f"AGGREGATE: {aggs}")
        
        # Add entities
        if self.entities:
            parts.append(f"ENTITIES: {', '.join(self.entities)}")
        
        # Add filters
        if self.filters:
            filters = ", ".join(f"{f.field} {f.operator.value} {f.value}" for f in self.filters)
            parts.append(f"FILTERS: {filters}")
        
        # Add time frame
        if self.time_frame:
            parts.append(f"TIME: {self.time_frame.start} to {self.time_frame.end}")
        
        # Add grouping
        if self.group_by:
            parts.append(f"GROUP BY: {', '.join(self.group_by)}")
        
        # Add ordering
        if self.order_by:
            orders = [f"{field} {order.value}" for field, order in self.order_by]
            parts.append(f"ORDER BY: {', '.join(orders)}")
        
        # Add limit
        if self.limit is not None:
            parts.append(f"LIMIT: {self.limit}")
        
        return " | ".join(parts)

class QueryIntent:
    def __init__(self):
        self.aggregation = None      # e.g., "COUNT", "SUM", "AVG", "MIN", "MAX"
        self.target_entity = None    # e.g., "לקוחות"
        self.target_field = None     # Specific field for aggregation (e.g., "גיל" for average age)
        self.filters = {}            # e.g., {"עיר": "מודיעין עילית", "תאריך": ">=2023-01-01"}
        self.group_by = None         # e.g., "עיר"
        self.order_by = None         # e.g., ("count", "DESC")
        self.limit = None            # e.g., 10 for top 10 results
        self.time_frame = None       # e.g., "last_30_days", "this_year"

    def __repr__(self):
        return (
            f"<QueryIntent: {self.aggregation} "
            f"{self.target_field or ''} {self.target_entity} "
            f"WHERE {self.filters} "
            f"GROUP BY {self.group_by} "
            f"ORDER BY {self.order_by} "
            f"LIMIT {self.limit}>"
        )


class EntityRecognizer:
    """Handles recognition of entities in the text with advanced BI capabilities"""
    
    def __init__(self, dictionary: TranslationDictionary):
        self.dictionary = dictionary
        
        # Location indicators and patterns
        self.location_indicators = {
            "ב", "ב-", "בעיר", "בעיר ", "בעיירה", "בכפר", "במושב", "בקיבוץ", 
            "בישוב", "במקום", "באזור", "במדינה", "בארץ", "בעולם"
        }
        
        # Date and time indicators
        self.date_indicators = {
            "מ-", "עד", "מיום", "עד יום", "מתאריך", "עד תאריך", "בחודש", 
            "בשנה", "מהתאריך", "עד התאריך", "מתחילת", "עד סוף", "בתאריך"
        }
        
        # Comparison operators with fuzzy matching support
        self.comparison_operators = {
            "יותר מ": ">", "פחות מ": "<", "מעל": ">", "מתחת": "<", 
            "שווה ל": "=", "אינו שווה ל": "!=", "שונה מ": "!=",
            "גדול מ": ">", "גדול או שווה ל": ">=", "קטן מ": "<",
            "קטן או שווה ל": "<=", "בין": "BETWEEN", "לא כולל": "!=",
            "בטווח": "BETWEEN", "בתוך": "IN"
        }
        
        # Time frames with fuzzy matching support
        self.time_frames = {
            "היום": "today",
            "אתמול": "yesterday",
            "מחר": "tomorrow",
            "שבוע שעבר": "last_week",
            "השבוע": "this_week",
            "שבוע הבא": "next_week",
            "חודש שעבר": "last_month",
            "החודש": "this_month",
            "חודש הבא": "next_month",
            "שנה שעברה": "last_year",
            "השנה": "this_year",
            "שנה הבאה": "next_year",
            "רבעון נוכחי": "this_quarter",
            "רבעון שעבר": "last_quarter",
            "רבעון הבא": "next_quarter",
            "30 הימים האחרונים": "last_30_days",
            "90 הימים האחרונים": "last_90_days",
            "365 הימים האחרונים": "last_365_days",
            "7 הימים האחרונים": "last_7_days",
            "14 הימים האחרונים": "last_14_days",
            "28 הימים האחרונים": "last_28_days"
        }
        
        # Common BI dimensions and measures
        self.bi_dimensions = {
            "תאריך": ["תאריך", "יום", "שבוע", "חודש", "שנה", "רבעון"],
            "עיר": ["עיר", "יישוב", "מקום", "איזור", "אזור", "מדינה", "ארץ"],
            "קטגוריה": ["קטגוריה", "סוג", "סיווג", "מחלקה", "קבוצה"],
            "מוצר": ["מוצר", "פריט", "סחורה", "מאמר", "פריטים"],
            "לקוח": ["לקוח", "משתמש", "צרכן", "איש קשר", "מנוי"],
            "ספק": ["ספק", "יצרן", "שותף", "מפיץ"],
            "עובד": ["עובד", "איש מכירות", "נציג", "אחראי"]
        }
        
        # Common BI measures
        self.bi_measures = {
            "כמות": ["כמות", "מספר", "סה""כ", "סהיכ""ל", "כמות כוללת"],
            "סכום": ["סכום", "סה""כ", "סך הכל", "סכ""כ", "סה""כ כספי"],
            "מחיר": ["מחיר", "עלות", "תמחיר", "מחירון", "שער"],
            "הנחה": ["הנחה", "הנחות", "קוד קופון", "קוד הנחה", "הנחת מבצע"],
            "מלאי": ["מלאי", "כמות במלאי", "זמינות", "כמות זמינה"],
            "דירוג": ["דירוג", "ציון", "ניקוד", "הערכה", "מדרג"],
            "ממוצע": ["ממוצע", "ממוצעי", "ממוצעת", "ממוצעים", "ממצוע"]
        }
        
        # Common time units
        self.time_units = {
            "שנייה": "second",
            "דקה": "minute",
            "שעה": "hour",
            "יום": "day",
            "שבוע": "week",
            "חודש": "month",
            "רבעון": "quarter",
            "שנה": "year"
        }
        
        # Common date formats with regex patterns
        self.date_patterns = [
            # DD/MM/YYYY or DD-MM-YYYY
            (r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', '%d/%m/%Y'),
            # DD/MM or DD-MM (assume current year)
            (r'(\d{1,2})[/-](\d{1,2})(?!\d)', '%d/%m'),
            # YYYY-MM-DD (ISO format)
            (r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', '%Y-%m-%d'),
            # Month names (e.g., 1 בינואר 2023)
            (r'(\d{1,2})\s+(בינואר|פברואר|מרץ|אפריל|מאי|יוני|יולי|אוגוסט|ספטמבר|אוקטובר|נובמבר|דצמבר)\s+(\d{4})', 
             lambda m: f"{m.group(1)} {self._hebrew_month_to_num(m.group(2))} {m.group(3)}",
             '%d %m %Y'),
            # Relative dates (e.g., לפני שבועיים, בעוד חודש)
            (r'(לפני|אחרי|בעוד)\s+(\d+)\s+(שניות|דקות|שעות|ימים|שבועות|חודשים|שנים)', 
             self._parse_relative_date)
        ]
        
        # Common BI entities with aliases
        self.bi_entities = {
            # Customers
            "לקוחות": ["אנשים", "משתמשים", "צרכנים", "מנויים", "אורחים", "רוכשים"],
            # Sales
            "מכירות": ["הזמנות", "רכישות", "תשלומים", "עסקאות", "מכירה", "קניות"],
            # Products
            "מוצרים": ["פריטים", "סחורה", "מלאי", "פריטי מדף", "סחורות"],
            # Invoices
            "חשבוניות": ["חשבוניות מס", "חשבוניות מכר", "חשבוניות רכישה", "חשבוניות ספק"],
            # Leads
            "לידים": ["פוטנציאלים", "לקוחות פוטנציאליים", "לידים", "לקוחות עתידיים"],
            # Support tickets
            "פניות": ["פניות שירות", "פניות תמיכה", "פניות לקוחות", "פניות שירות"]
        }
        
        # Common aggregations
        self.aggregation_terms = {
            "COUNT": ["כמה", "מספר", "כמות", "סה""כ", "סך הכל"],
            "SUM": ["סך", "סכום", "סיכום", "סה""כ של", "סכ""כ"],
            "AVG": ["ממוצע", "ממוצע של", "ממוצעי", "ממוצעת"],
            "MIN": ["מינימום", "הכי נמוך", "הנמוך ביותר", "הקטן ביותר"],
            "MAX": ["מקסימום", "הכי גבוה", "הגבוה ביותר", "הגדול ביותר"],
            "COUNT_DISTINCT": ["מספר ייחודי של", "כמה ייחודיים", "כמה שונים"],
            "MEDIAN": ["חציון", "ערך אמצעי", "ערך חציון"],
            "STDDEV": ["סטיית תקן", "פיזור", "שונות"],
            "VARIANCE": ["שונות", "פיזור", "הפרש"],
            "PERCENTILE": ["אחוזון", "אחוזון ה-", "אחוזון מס"],
            "FIRST": ["הראשון", "הערך הראשון", "התוצאה הראשונה"],
            "LAST": ["האחרון", "הערך האחרון", "התוצאה האחרונה"]
        }
        
        # Common time expressions
        self.time_expressions = {
            "היום בבוקר": lambda: (datetime.now().replace(hour=0, minute=0, second=0), 
                                   datetime.now().replace(hour=12, minute=0, second=0)),
            "אתמול בערב": lambda: (datetime.now().replace(hour=18, minute=0, second=0) - timedelta(days=1),
                                   datetime.now().replace(hour=23, minute=59, second=59) - timedelta(days=1)),
            "סוף השבוע שעבר": lambda: self._get_weekend_range(weeks_ago=1),
            "סוף השבוע הנוכחי": lambda: self._get_weekend_range(weeks_ago=0),
            "תחילת החודש": lambda: (datetime.now().replace(day=1, hour=0, minute=0, second=0),
                                   datetime.now().replace(day=1, hour=23, minute=59, second=59)),
            "אמצע החודש": lambda: self._get_middle_of_month(),
            "סוף החודש": lambda: self._get_end_of_month(),
            "תחילת הרבעון": lambda: self._get_quarter_start(),
            "סוף הרבעון": lambda: self._get_quarter_end(),
            "תחילת השנה": lambda: (datetime.now().replace(month=1, day=1, hour=0, minute=0, second=0),
                                  datetime.now().replace(month=1, day=1, hour=23, minute=59, second=59)),
            "אמצע השנה": lambda: (datetime.now().replace(month=7, day=1, hour=0, minute=0, second=0),
                                 datetime.now().replace(month=7, day=31, hour=23, minute=59, second=59)),
            "סוף השנה": lambda: (datetime.now().replace(month=12, day=31, hour=23, minute=59, second=59),
                                datetime.now().replace(month=12, day=31, hour=23, minute=59, second=59))
        }
        
        # Initialize fuzzy matcher
        self._init_fuzzy_matcher()
    
    def _init_fuzzy_matcher(self):
        """Initialize fuzzy matching components"""
        # Create a flat list of all terms for fuzzy matching
        self._all_terms = {}
        
        # Add entities and their aliases
        for entity, aliases in self.bi_entities.items():
            self._all_terms[entity] = "entity"
            for alias in aliases:
                self._all_terms[alias] = f"entity:{entity}"
        
        # Add dimensions and their aliases
        for dim, aliases in self.bi_dimensions.items():
            self._all_terms[dim] = f"dimension:{dim}"
            for alias in aliases:
                self._all_terms[alias] = f"dimension:{dim}"
        
        # Add measures and their aliases
        for measure, aliases in self.bi_measures.items():
            self._all_terms[measure] = f"measure:{measure}"
            for alias in aliases:
                self._all_terms[alias] = f"measure:{measure}"
        
        # Add time units
        for hebrew, english in self.time_units.items():
            self._all_terms[hebrew] = f"time_unit:{english}"
    
    def _get_weekend_range(self, weeks_ago: int = 0) -> tuple:
        """Get the datetime range for a weekend (Friday to Saturday)"""
        today = datetime.now() - timedelta(weeks=weeks_ago)
        # Find the most recent Friday
        days_since_friday = (today.weekday() - 4) % 7
        friday = today - timedelta(days=days_since_friday + (7 * weeks_ago))
        saturday = friday + timedelta(days=1)
        
        return (
            friday.replace(hour=0, minute=0, second=0),
            saturday.replace(hour=23, minute=59, second=59)
        )
    
    def _get_middle_of_month(self) -> tuple:
        """Get the middle of the current month"""
        today = datetime.now()
        middle_day = 15
        start = today.replace(day=middle_day, hour=0, minute=0, second=0)
        
        # Handle months with fewer than 31 days
        try:
            end = today.replace(day=middle_day, hour=23, minute=59, second=59)
        except ValueError:
            end = start + timedelta(days=1) - timedelta(seconds=1)
        
        return (start, end)
    
    def _get_end_of_month(self) -> tuple:
        """Get the end of the current month"""
        today = datetime.now()
        next_month = today.replace(day=28) + timedelta(days=4)  # This will never fail
        last_day = next_month - timedelta(days=next_month.day)
        
        return (
            last_day.replace(hour=0, minute=0, second=0),
            last_day.replace(hour=23, minute=59, second=59)
        )
    
    def _get_quarter_start(self) -> datetime:
        """Get the start of the current quarter"""
        today = datetime.now()
        month = today.month
        quarter_start_month = 3 * ((month - 1) // 3) + 1
        return today.replace(month=quarter_start_month, day=1, hour=0, minute=0, second=0)
    
    def _get_quarter_end(self) -> datetime:
        """Get the end of the current quarter"""
        today = datetime.now()
        month = today.month
        quarter_end_month = 3 * ((month - 1) // 3 + 1)
        next_quarter_month = quarter_end_month % 12 + 1
        next_quarter_year = today.year + (1 if quarter_end_month == 12 else 0)
        
        return datetime(
            next_quarter_year, next_quarter_month, 1,
            hour=23, minute=59, second=59
        ) - timedelta(days=1)
    
    def _hebrew_month_to_num(self, month_hebrew: str) -> int:
        """Convert Hebrew month name to month number (1-12)"""
        months = {
            'ינואר': 1, 'פברואר': 2, 'מרץ': 3, 'אפריל': 4, 'מאי': 5, 'יוני': 6,
            'יולי': 7, 'אוגוסט': 8, 'ספטמבר': 9, 'אוקטובר': 10, 'נובמבר': 11, 'דצמבר': 12
        }
        return months.get(month_hebrew, 1)
    
    def _parse_relative_date(self, match) -> Optional[tuple]:
        """Parse relative date expressions like 'לפני שבועיים'"""
        direction = match.group(1)
        value = int(match.group(2))
        unit = match.group(3)
        
        # Map Hebrew units to timedelta arguments
        unit_map = {
            'שניות': 'seconds', 'דקות': 'minutes', 'שעות': 'hours',
            'ימים': 'days', 'שבועות': 'weeks', 'חודשים': 'months', 'שנים': 'years'
        }
        
        if unit not in unit_map:
            return None
        
        # Calculate the delta
        delta_args = {unit_map[unit]: value * (-1 if direction == 'לפני' else 1)}
        
        if unit in ['חודשים', 'שנים']:
            # For months and years, we need to use relativedelta
            from dateutil.relativedelta import relativedelta
            delta = relativedelta(**{unit_map[unit]: delta_args[unit_map[unit]]})
            result = datetime.now() + delta
        else:
            # For other units, we can use timedelta
            delta = timedelta(**delta_args)
            result = datetime.now() + delta
        
        return (result.strftime('%Y-%m-%d %H:%M:%S'),)
    
    def find_entity(self, text: str, threshold: float = 0.8) -> Optional[str]:
        """Find the main entity in the text with fuzzy matching"""
        # First check for exact matches in canonical terms
        for term in self.dictionary._by_canonical:
            if term in text:
                return term
        
        # Then check aliases with fuzzy matching
        best_match = None
        best_score = threshold
        
        for term, canonical in self._all_terms.items():
            # Skip if term is too short for meaningful matching
            if len(term) < 3:
                continue
                
            # Use partial ratio for better substring matching
            score = fuzz.partial_ratio(term.lower(), text.lower()) / 100.0
            
            if score > best_score:
                best_score = score
                best_match = canonical.split(':')[-1]  # Get the base canonical term
        
        if best_match:
            return best_match
        
        # Fall back to common BI entities if no match found
        for canonical, aliases in self.bi_entities.items():
            if any(alias in text for alias in [canonical] + aliases):
                return canonical
                
        return None
    
    def extract_locations(self, text: str) -> Dict[str, str]:
        """Extract location filters from text with improved accuracy"""
        locations = {}
        words = text.split()
        
        for i, word in enumerate(words):
            # Check for location indicators
            if word in self.location_indicators and i + 1 < len(words):
                location_parts = []
                j = i + 1
                
                # Collect all words that are part of the location
                while j < len(words):
                    next_word = words[j]
                    
                    # Stop if we hit another indicator or certain stop words
                    if (next_word in self.location_indicators.union(self.date_indicators) or
                        next_word in ['ב', 'ל', 'מ', 'עם', 'עד', 'על', 'של', 'כמה', 'מה', 'איפה']):
                        break
                        
                    location_parts.append(next_word)
                    j += 1
                
                if location_parts:
                    location = ' '.join(location_parts)
                    # Clean up the location (remove punctuation, etc.)
                    location = re.sub(r'[.,:;!?\'"()]', '', location).strip()
                    if location:
                        # Try to determine the type of location
                        if any(term in location for term in ['עיר', 'יישוב', 'ישוב', 'עיירה']):
                            locations['עיר'] = location
                        elif any(term in location for term in ['ארץ', 'מדינה']):
                            locations['מדינה'] = location
                        elif any(term in location for term in ['אזור', 'איזור', 'מחוז']):
                            locations['אזור'] = location
                        else:
                            # Default to city if type can't be determined
                            locations['עיר'] = location
        
        return locations
    
    def extract_dates(self, text: str) -> Dict[str, Any]:
        """Extract date filters from text with support for complex expressions"""
        dates = {}
        
        # First check for predefined time frames
        for hebrew_time, frame in self.time_frames.items():
            if hebrew_time in text:
                dates["time_frame"] = frame
                return dates
        
        # Check for time expressions
        for expr, func in self.time_expressions.items():
            if expr in text:
                try:
                    start, end = func()
                    dates["start_date"] = start
                    dates["end_date"] = end
                    dates["is_range"] = True
                    return dates
                except (ValueError, TypeError):
                    continue
        
        # Extract specific dates using patterns
        for pattern in self.date_patterns:
            if len(pattern) == 2:  # Simple pattern with format
                regex, date_format = pattern
                for match in re.finditer(regex, text):
                    try:
                        date_str = match.group(0)
                        date = datetime.strptime(date_str, date_format)
                        # If no year is specified, assume current year
                        if date.year == 1900:
                            date = date.replace(year=datetime.now().year)
                        dates["date"] = date.strftime('%Y-%m-%d')
                        return dates
                    except (ValueError, AttributeError):
                        continue
            elif len(pattern) == 3:  # Pattern with transformation
                regex, transform, date_format = pattern
                for match in re.finditer(regex, text):
                    try:
                        if callable(transform):
                            # Apply transformation to the matched text
                            transformed = transform(match)
                            if isinstance(transformed, tuple):
                                date = datetime.strptime(transformed[0], date_format)
                            else:
                                date = datetime.strptime(transformed, date_format)
                            dates["date"] = date.strftime('%Y-%m-%d')
                            return dates
                    except (ValueError, AttributeError, IndexError):
                        continue
        
        # Handle relative dates (e.g., "לפני שלושה ימים")
        relative_date_match = re.search(
            r'(לפני|אחרי|בעוד)\s+(\d+)\s+(שניות|דקות|שעות|ימים|שבועות|חודשים|שנים)',
            text
        )
        
        if relative_date_match:
            direction = relative_date_match.group(1)
            value = int(relative_date_match.group(2))
            unit = relative_date_match.group(3)
            
            # Map Hebrew units to timedelta arguments
            unit_map = {
                'שניות': 'seconds', 'דקות': 'minutes', 'שעות': 'hours',
                'ימים': 'days', 'שבועות': 'weeks', 'חודשים': 'months', 'שנים': 'years'
            }
            
            if unit in unit_map:
                delta_args = {unit_map[unit]: value * (-1 if direction == 'לפני' else 1)}
                
                if unit in ['חודשים', 'שנים']:
                    # For months and years, use relativedelta
                    from dateutil.relativedelta import relativedelta
                    delta = relativedelta(**{unit_map[unit]: delta_args[unit_map[unit]]})
                    result = datetime.now() + delta
                else:
                    # For other units, use timedelta
                    delta = timedelta(**delta_args)
                    result = datetime.now() + delta
                
                dates["date"] = result.strftime('%Y-%m-%d %H:%M:%S')
        
        return dates
    
    def extract_comparisons(self, text: str) -> Dict[str, Any]:
        """Extract comparison operators and values with support for complex expressions"""
        comparisons = {}
        
        # First, try to find comparison patterns
        for hebrew_op, op in self.comparison_operators.items():
            if hebrew_op in text:
                try:
                    # Extract the text after the operator
                    after_op = text.split(hebrew_op, 1)[1].strip()
                    
                    # Find the end of the value (next operator or end of string)
                    next_op_pos = min(
                        [after_op.find(op) for op in self.comparison_operators.keys() 
                         if op in after_op] or [len(after_op)])
                    value_text = after_op[:next_op_pos].strip()
                    
                    # Clean up the value text
                    value_text = re.sub(r'[.,:;!?\'"()]', '', value_text).split()[0]
                    
                    if value_text:
                        # Try to convert to number if possible
                        try:
                            if '.' in value_text:
                                value = float(value_text)
                            else:
                                value = int(value_text)
                        except ValueError:
                            value = value_text
                        
                        # For BETWEEN operator, we need two values
                        if op == 'BETWEEN' and 'ו' in after_op:
                            parts = after_op.split('ו', 1)
                            if len(parts) == 2:
                                try:
                                    val1 = float(parts[0].strip())
                                    val2 = float(parts[1].split()[0].strip())
                                    value = (min(val1, val2), max(val1, val2))
                                except (ValueError, IndexError):
                                    pass
                        
                        # Find the field being compared
                        before_op = text.split(hebrew_op)[0].strip().rsplit(maxsplit=1)[-1]
                        field = before_op if before_op in self._all_terms else None
                        
                        comparisons[field or "value"] = {
                            "operator": op,
                            "value": value,
                            "field": field
                        }
                except (IndexError, ValueError) as e:
                    logger.debug(f"Error extracting comparison: {e}")
                    continue
        
        # Also look for numeric ranges (e.g., "בין 100 ל-200")
        range_match = re.search(r'בין\s+(\d+)\s+ל[\s-](\d+)', text)
        if range_match:
            try:
                val1 = float(range_match.group(1))
                val2 = float(range_match.group(2))
                comparisons["value"] = {
                    "operator": "BETWEEN",
                    "value": (min(val1, val2), max(val1, val2)),
                    "field": None
                }
            except (ValueError, IndexError):
                pass
        
        return comparisons
    
    def extract_aggregations(self, text: str) -> List[Dict[str, Any]]:
        """Extract aggregation operations from text"""
        aggregations = []
        
        # Look for aggregation patterns
        for agg_type, terms in self.aggregation_terms.items():
            for term in terms:
                if term in text:
                    # Find the field being aggregated
                    after_term = text.split(term, 1)[1].strip()
                    field = None
                    
                    # Look for a field name after the aggregation term
                    for possible_field in self._all_terms:
                        if possible_field in after_term.split()[:3]:  # Check first few words
                            field = possible_field
                            break
                    
                    aggregations.append({
                        "type": agg_type,
                        "field": field,
                        "term": term
                    })
        
        return aggregations
    
    def extract_dimensions(self, text: str) -> List[str]:
        """Extract dimension fields for grouping"""
        dimensions = []
        
        # Look for dimension indicators
        group_indicators = ["לפי", "על פי", "מחולק לפי", "מקובץ לפי", "מסודר לפי"]
        
        for indicator in group_indicators:
            if indicator in text:
                # Get the text after the indicator
                parts = text.split(indicator, 1)
                if len(parts) > 1:
                    # Take the next few words as potential dimension names
                    words = parts[1].strip().split()
                    for word in words[:3]:  # Check first 3 words after indicator
                        word = re.sub(r'[.,:;!?\'"()]', '', word)
                        if word in self._all_terms:
                            dimensions.append(word)
        
        # Also look for dimension names directly in the text
        for dim in self.bi_dimensions:
            if dim in text and dim not in dimensions:
                dimensions.append(dim)
        
        return dimensions
    
    def extract_measures(self, text: str) -> List[str]:
        """Extract measure fields for aggregation"""
        measures = []
        
        # Look for measure names in the text
        for measure in self.bi_measures:
            if measure in text and measure not in measures:
                measures.append(measure)
        
        return measures
    
    def extract_time_dimension(self, text: str) -> Optional[str]:
        """Extract time dimension field"""
        time_terms = ["תאריך", "זמן", "שעה", "יום", "חודש", "שנה", "רבעון"]
        
        for term in time_terms:
            if term in text:
                return term
        
        return None
    
    def extract_limit(self, text: str) -> Optional[int]:
        """Extract result limit from text"""
        # Look for patterns like "10 הראשונים"
        limit_match = re.search(r'(\d+)\s*(הראשונים|העליונים|האחרונים|התחתונים)', text)
        if limit_match:
            try:
                return int(limit_match.group(1))
            except (ValueError, IndexError):
                pass
        
        # Look for patterns like "רק 5 תוצאות"
        only_match = re.search(r'רק\s+(\d+)', text)
        if only_match:
            try:
                return int(only_match.group(1))
            except (ValueError, IndexError):
                pass
        
        return None
    
    def extract_sort_order(self, text: str) -> List[Tuple[str, str]]:
        """Extract sort order from text"""
        sort_orders = []
        
        # Look for sort indicators
        sort_indicators = ["מיין לפי", "סדר לפי", "מסודר לפי", "מיין ב"]
        
        for indicator in sort_indicators:
            if indicator in text:
                # Get the text after the indicator
                parts = text.split(indicator, 1)
                if len(parts) > 1:
                    # Take the next few words as potential sort fields
                    sort_text = parts[1].strip()
                    
                    # Determine sort direction
                    if any(word in sort_text for word in ["עולה", "קטן לגדול", "א-ת"]):
                        direction = "ASC"
                    elif any(word in sort_text for word in ["יורד", "גדול לקטן", "ת-א"]):
                        direction = "DESC"
                    else:
                        # Default to DESC for common cases like "הכי גבוה"
                        direction = "DESC" if any(word in text for word in ["גבוה", "גדול", "הכי"]) else "ASC"
                    
                    # Extract field names
                    for field in self._all_terms:
                        if field in sort_text.split()[:3]:  # Check first few words
                            sort_orders.append((field, direction))
                            break
        
        return sort_orders
    
    def extract_filters(self, text: str) -> List[Dict[str, Any]]:
        """Extract all filters from text"""
        filters = []
        
        # Extract locations
        locations = self.extract_locations(text)
        for field, value in locations.items():
            filters.append({
                "field": field,
                "operator": "=",
                "value": value
            })
        
        # Extract dates
        dates = self.extract_dates(text)
        if "date" in dates:
            filters.append({
                "field": "תאריך",
                "operator": "=",
                "value": dates["date"]
            })
        elif "start_date" in dates and "end_date" in dates:
            filters.append({
                "field": "תאריך",
                "operator": "BETWEEN",
                "value": (dates["start_date"], dates["end_date"])
            })
        
        # Extract comparisons
        comparisons = self.extract_comparisons(text)
        for field, comp in comparisons.items():
            filters.append({
                "field": field or comp.get("field", "value"),
                "operator": comp["operator"],
                "value": comp["value"]
            })
        
        return filters


class IntentClassifier:
    """Classifies the intent of BI queries with advanced capabilities"""
    
    def __init__(self):
        # Aggregation terms with weights for fuzzy matching
        self.aggregation_terms = {
            AggregationType.COUNT: {
                "terms": ["כמה", "מספר", "כמות", "סך הכל", "סה""כ", "כמות כוללת"],
                "weight": 1.0
            },
            AggregationType.SUM: {
                "terms": ["סך", "סה""כ", "סכום", "סיכום", "סך הכל", "סה""כ כספי"],
                "weight": 1.0
            },
            AggregationType.AVG: {
                "terms": ["ממוצע", "ממוצע של", "ממוצעי", "ממוצעת", "ממוצעים", "ממצוע"],
                "weight": 1.0
            },
            AggregationType.MIN: {
                "terms": ["מינימום", "הכי נמוך", "הנמוך ביותר", "הקטן ביותר", "המוקדם ביותר"],
                "weight": 0.9
            },
            AggregationType.MAX: {
                "terms": ["מקסימום", "הכי גבוה", "הגבוה ביותר", "הגדול ביותר", "האחרון"],
                "weight": 0.9
            },
            AggregationType.COUNT_DISTINCT: {
                "terms": ["מספר ייחודי של", "כמה ייחודיים", "כמה שונים", "ספירת ערכים ייחודיים"],
                "weight": 0.8
            },
            AggregationType.MEDIAN: {
                "terms": ["חציון", "ערך אמצעי", "ערך חציון"],
                "weight": 0.7
            },
            AggregationType.STDDEV: {
                "terms": ["סטיית תקן", "פיזור", "שונות"],
                "weight": 0.6
            },
            AggregationType.VARIANCE: {
                "terms": ["שונות", "פיזור", "הפרש"],
                "weight": 0.6
            },
            AggregationType.PERCENTILE: {
                "terms": ["אחוזון", "אחוזון ה-", "אחוזון מס"],
                "weight": 0.5
            }
        }
        
        # Indicators for different query components
        self.group_indicators = ["לפי", "על פי", "מחולק לפי", "מקובץ לפי", "מסודר לפי", "לפי קטגוריית"]
        self.order_indicators = ["מיין לפי", "סדר לפי", "הצג לפי סדר", "מיין ב", "מסודר לפי"]
        self.limit_indicators = ["הראשונים", "העליונים", "התחתונים", "רק", "רק את", "לכל היותר"]
        self.filter_indicators = ["שבו", "שבה", "שבין", "שמתאימים ל", "שעונים על", "עם", "בין"]
        self.comparison_indicators = ["גדול מ", "קטן מ", "שווה ל", "שונה מ", "דומה ל", "בטווח", "בין"]
        
        # Common BI patterns
        self.bi_patterns = {
            "top_n": r"(הצג|הראה|חפש)\s*(את)?\s*(ה)?(\d+)\s*(הראשונים|העליונים|הטובים ביותר|הגבוהים ביותר)",
            "trend": r"(מגמה|מגמות|התפתחות|שינוי|גרף|טרנד|סטטיסטיקה)",
            "comparison": r"(לעומת|מול|בהשוואה ל|בהשוואה ל|יחסית ל|מול ה)",
            "distribution": r"(חלוקה|פילוח|התפלגות|אחוז|אחוזים|אחוזי|אחוז מ|אחוזים מ)",
            "correlation": r"(קשר|התאמה|קורלציה|תלות|השפעה|השפעות)"
        }
        
        # Initialize fuzzy matcher
        self._init_fuzzy_matcher()
    
    def _init_fuzzy_matcher(self):
        """Initialize fuzzy matching components"""
        # Create a flat list of all terms for fuzzy matching
        self._all_terms = {}
        
        # Add aggregation terms
        for agg_type, data in self.aggregation_terms.items():
            for term in data["terms"]:
                self._all_terms[term] = f"agg:{agg_type.value}"
        
        # Add indicators
        for indicator in (self.group_indicators + self.order_indicators + 
                         self.limit_indicators + self.filter_indicators + 
                         self.comparison_indicators):
            self._all_terms[indicator] = f"indicator:{indicator}"
    
    def classify_aggregation(self, text: str, context: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Determine the aggregation types from the text with confidence scores"""
        text = text.lower()
        results = []
        
        # First check for exact matches
        for agg_type, data in self.aggregation_terms.items():
            for term in data["terms"]:
                if term in text:
                    results.append({
                        "type": agg_type,
                        "confidence": 1.0 * data["weight"],
                        "term": term,
                        "method": "exact_match"
                    })
        
        # If no exact matches found, try fuzzy matching
        if not results:
            words = text.split()
            for word in words:
                # Skip short words
                if len(word) < 3:
                    continue
                    
                # Find the best matching term
                best_match = None
                best_score = 0.7  # Minimum threshold
                
                for term, term_type in self._all_terms.items():
                    if not term_type.startswith("agg:"):
                        continue
                        
                    # Calculate similarity score
                    score = fuzz.ratio(word.lower(), term.lower()) / 100.0
                    
                    # Apply length-based penalty for very different lengths
                    length_ratio = len(word) / len(term) if len(word) < len(term) else len(term) / len(word)
                    score *= length_ratio
                    
                    if score > best_score:
                        best_score = score
                        best_match = (term, term_type)
                
                if best_match:
                    term, term_type = best_match
                    agg_type = term_type.split(":")[1]
                    results.append({
                        "type": AggregationType(agg_type),
                        "confidence": best_score,
                        "term": term,
                        "method": "fuzzy_match"
                    })
        
        # Sort by confidence (highest first)
        results.sort(key=lambda x: x["confidence"], reverse=True)
        
        # If still no matches, return default COUNT with lower confidence
        if not results and (context is None or not context.get("has_explicit_aggregation", False)):
            return [{
                "type": AggregationType.COUNT,
                "confidence": 0.5,
                "term": "default",
                "method": "default"
            }]
        
        return results
    
    def extract_group_by(self, text: str, entities: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Extract group by fields from text with confidence scores"""
        groups = []
        
        # Look for group indicators
        for indicator in self.group_indicators:
            if indicator in text:
                # Get the text after the indicator
                parts = text.split(indicator, 1)
                if len(parts) > 1:
                    # Take the next few words as potential group fields
                    group_text = parts[1].strip()
                    
                    # Look for field names in the text after the indicator
                    for entity in (entities or []):
                        if entity in group_text.split()[:3]:  # Check first few words
                            groups.append({
                                "field": entity,
                                "confidence": 0.9,
                                "indicator": indicator
                            })
        
        return groups
    
    def extract_order_by(self, text: str, entities: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Extract order by clauses from text with confidence scores"""
        orders = []
        
        # Look for order indicators
        for indicator in self.order_indicators:
            if indicator in text:
                # Get the text after the indicator
                parts = text.split(indicator, 1)
                if len(parts) > 1:
                    # Take the next few words as potential sort fields
                    sort_text = parts[1].strip()
                    
                    # Determine sort direction with confidence
                    if any(word in sort_text for word in ["עולה", "קטן לגדול", "א-ת", "מהקטן לגדול"]):
                        direction = SortOrder.ASC
                        direction_confidence = 0.9
                    elif any(word in sort_text for word in ["יורד", "גדול לקטן", "ת-א", "מהגדול לקטן"]):
                        direction = SortOrder.DESC
                        direction_confidence = 0.9
                    else:
                        # Default to DESC for common cases like "הכי גבוה"
                        if any(word in text for word in ["גבוה", "גדול", "הכי", "טוב", "מעולה"]):
                            direction = SortOrder.DESC
                            direction_confidence = 0.7
                        else:
                            direction = SortOrder.ASC
                            direction_confidence = 0.6
                    
                    # Extract field names with confidence
                    for entity in (entities or []):
                        if entity in sort_text.split()[:3]:  # Check first few words
                            orders.append({
                                "field": entity,
                                "direction": direction,
                                "confidence": direction_confidence * 0.9,  # Slightly reduce confidence
                                "indicator": indicator
                            })
        
        return orders
    
    def extract_limit(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract limit from text with confidence"""
        # Look for patterns like "10 הראשונים"
        limit_match = re.search(r'(\d+)\s*(הראשונים|העליונים|האחרונים|התחתונים)', text)
        if limit_match:
            try:
                return {
                    "limit": int(limit_match.group(1)),
                    "confidence": 0.9,
                    "method": "explicit_count"
                }
            except (ValueError, IndexError):
                pass
        
        # Look for patterns like "רק 5 תוצאות"
        only_match = re.search(r'רק\s+(\d+)', text)
        if only_match:
            try:
                return {
                    "limit": int(only_match.group(1)),
                    "confidence": 0.8,
                    "method": "only_x"
                }
            except (ValueError, IndexError):
                pass
        
        # Look for top-N patterns
        top_match = re.search(r'(הצג|הראה|חפש)\s*(את)?\s*(ה)?(\d+)', text)
        if top_match:
            try:
                return {
                    "limit": int(top_match.group(4)),
                    "confidence": 0.7,
                    "method": "top_n"
                }
            except (ValueError, IndexError):
                pass
        
        return None
    
    def classify_query_type(self, text: str) -> Dict[str, float]:
        """Classify the type of BI query with confidence scores"""
        scores = {
            "trend": 0.0,      # Time-based trends
            "comparison": 0.0,  # Compare metrics
            "ranking": 0.0,     # Top/bottom N
            "breakdown": 0.0,   # Group by dimensions
            "distribution": 0.0,# Percentage/ratio
            "correlation": 0.0, # Relationships
            "drilldown": 0.0,   # Detailed view
            "overview": 0.0     # General summary
        }
        
        text_lower = text.lower()
        
        # Check for trend indicators
        trend_terms = ["מגמה", "טרנד", "לאורך זמן", "במהלך", "בחודשים האחרונים", "בשנה האחרונה"]
        if any(term in text_lower for term in trend_terms):
            scores["trend"] += 0.8
        
        # Check for comparison indicators
        comparison_terms = ["לעומת", "מול", "בהשוואה", "יחסית", "יותר מ", "פחות מ"]
        if any(term in text_lower for term in comparison_terms):
            scores["comparison"] += 0.9
        
        # Check for ranking indicators
        ranking_terms = ["הכי", "הכי הרבה", "הכי פחות", "הטובים ביותר", "הגרועים ביותר"]
        if any(term in text_lower for term in ranking_terms):
            scores["ranking"] += 0.8
        
        # Check for breakdown indicators
        breakdown_terms = ["לפי", "מחולק לפי", "לפי קטגוריה", "לכל אחד מ"]
        if any(term in text_lower for term in breakdown_terms):
            scores["breakdown"] += 0.9
        
        # Check for distribution indicators
        distribution_terms = ["אחוז", "אחוזים", "חלק", "חלוקה", "התפלגות"]
        if any(term in text_lower for term in distribution_terms):
            scores["distribution"] += 0.8
        
        # Check for correlation indicators
        correlation_terms = ["קשר", "התאמה", "קורלציה", "תלות", "השפעה"]
        if any(term in text_lower for term in correlation_terms):
            scores["correlation"] += 0.9
        
        # Check for drilldown indicators
        drilldown_terms = ["פרטי", "מפורט", "לראות את כל", "להציג פרטים"]
        if any(term in text_lower for term in drilldown_terms):
            scores["drilldown"] += 0.8
        
        # If no specific type detected, it's likely an overview
        if max(scores.values()) < 0.5:
            scores["overview"] = 0.7
        
        # Normalize scores to sum to 1.0
        total = sum(scores.values())
        if total > 0:
            scores = {k: v/total for k, v in scores.items()}
        
        return scores


class NLPProcessor:
    """Processes natural language questions into structured query intents with advanced BI capabilities"""
    
    def __init__(self, dictionary: Optional[TranslationDictionary] = None):
        self.dictionary = dictionary or TranslationDictionary()
        self.entity_recognizer = EntityRecognizer(self.dictionary)
        self.intent_classifier = IntentClassifier()
        self.context = {}
    
    def process_question(self, question: str, context: Optional[Dict] = None) -> QueryIntent:
        """
        Process a natural language question and extract a structured query intent
        
        Args:
            question: The natural language question to process
            context: Optional context from previous interactions
            
        Returns:
            QueryIntent: A structured representation of the query intent
        """
        # Initialize intent with default values
        intent = QueryIntent()
        question = question.strip()
        
        # Update context with any provided context
        if context:
            self.context.update(context)
        
        # 1. Extract entities and dimensions
        entities = self._extract_entities(question)
        dimensions = self._extract_dimensions(question)
        measures = self._extract_measures(question)
        
        # 2. Determine query type and intent
        query_type = self.intent_classifier.classify_query_type(question)
        intent.metadata["query_type"] = max(query_type.items(), key=lambda x: x[1])[0]
        
        # 3. Extract aggregations
        self._extract_aggregations(intent, question, measures)
        
        # 4. Extract filters and conditions
        self._extract_filters(intent, question)
        
        # 5. Handle time dimensions and time-based queries
        self._handle_time_dimension(intent, question)
        
        # 6. Extract grouping
        self._extract_grouping(intent, question, dimensions)
        
        # 7. Extract sorting and ordering
        self._extract_ordering(intent, question, entities + dimensions + measures)
        
        # 8. Extract result limits
        self._extract_limits(intent, question)
        
        # 9. Apply any context from previous interactions
        self._apply_context(intent)
        
        # 10. Validate and clean up the intent
        self._validate_intent(intent)
        
        # Update context for follow-up questions
        self._update_context(intent)
        
        return intent
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract entities from the text"""
        # Use the entity recognizer to find entities
        entities = []
        
        # Find main entities (e.g., "לקוחות", "מוצרים")
        main_entity = self.entity_recognizer.find_entity(text)
        if main_entity:
            entities.append(main_entity)
        
        # Also look for other entities that might be referenced
        for entity in self.entity_recognizer.bi_entities:
            if entity in text and entity not in entities:
                entities.append(entity)
        
        return entities
    
    def _extract_dimensions(self, text: str) -> List[str]:
        """Extract dimension fields from the text"""
        return self.entity_recognizer.extract_dimensions(text)
    
    def _extract_measures(self, text: str) -> List[str]:
        """Extract measure fields from the text"""
        return self.entity_recognizer.extract_measures(text)
    
    def _extract_aggregations(self, intent: QueryIntent, text: str, measures: List[str]) -> None:
        """Extract aggregation operations from the text"""
        # Get aggregations with confidence scores
        aggregations = self.intent_classifier.classify_aggregation(text, self.context)
        
        if not aggregations:
            # Default to COUNT if no aggregation specified
            intent.aggregations.append(Aggregation(
                field="*",
                operation=AggregationType.COUNT
            ))
            return
        
        # Add aggregations to the intent
        for agg in aggregations:
            agg_type = agg["type"]
            confidence = agg["confidence"]
            
            # Find the field for this aggregation
            field = None
            
            # If we have measures, try to match them with the aggregation
            if measures:
                # For now, just take the first measure
                field = measures[0]
            
            # If no measure found, use a default based on aggregation type
            if not field:
                if agg_type == AggregationType.COUNT:
                    field = "*"  # Count all rows
                else:
                    # For other aggregations, we need a field
                    # This could be improved by looking at the context or schema
                    field = "סכום" if agg_type == AggregationType.SUM else "ערך"
            
            # Add the aggregation to the intent
            intent.aggregations.append(Aggregation(
                field=field,
                operation=agg_type,
                alias=f"{agg_type.value.lower()}_{field}"
            ))
    
    def _extract_filters(self, intent: QueryIntent, text: str) -> None:
        """Extract filter conditions from the text"""
        # Extract locations
        locations = self.entity_recognizer.extract_locations(text)
        for field, value in locations.items():
            intent.filters.append(FilterCondition(
                field=field,
                operator=ComparisonOperator.EQUALS,
                value=value
            ))
        
        # Extract dates
        dates = self.entity_recognizer.extract_dates(text)
        if "date" in dates:
            intent.filters.append(FilterCondition(
                field="תאריך",
                operator=ComparisonOperator.EQUALS,
                value=dates["date"]
            ))
        elif "start_date" in dates and "end_date" in dates:
            intent.filters.append(FilterCondition(
                field="תאריך",
                operator=ComparisonOperator.BETWEEN,
                value=(dates["start_date"], dates["end_date"])
            ))
        
        # Extract comparisons
        comparisons = self.entity_recognizer.extract_comparisons(text)
        for field, comp in comparisons.items():
            intent.filters.append(FilterCondition(
                field=field or comp.get("field", "value"),
                operator=ComparisonOperator(comp["operator"]),
                value=comp["value"]
            ))
    
    def _handle_time_dimension(self, intent: QueryIntent, text: str) -> None:
        """Handle time dimensions and time-based queries"""
        # Check if there's a time dimension in the text
        time_dim = self.entity_recognizer.extract_time_dimension(text)
        
        if time_dim:
            intent.time_dimension = time_dim
            
            # If we have a time dimension but no date filters, add a default time frame
            if not any(f.field == "תאריך" for f in intent.filters):
                # Default to last 30 days
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                intent.filters.append(FilterCondition(
                    field="תאריך",
                    operator=ComparisonOperator.GREATER_OR_EQUAL,
                    value=start_date
                ))
    
    def _extract_grouping(self, intent: QueryIntent, text: str, dimensions: List[str]) -> None:
        """Extract grouping information from the text"""
        # Extract group by fields
        group_by = self.intent_classifier.extract_group_by(text, dimensions)
        
        # Add group by fields to intent
        for group in group_by:
            if group["field"] not in intent.group_by:
                intent.group_by.append(group["field"])
        
        # If we have aggregations but no explicit grouping, and we have dimensions,
        # consider adding them as groups
        if intent.aggregations and not intent.group_by and dimensions:
            intent.group_by.extend(dimensions[:2])  # Add up to 2 dimensions as groups
    
    def _extract_ordering(self, intent: QueryIntent, text: str, fields: List[str]) -> None:
        """Extract ordering information from the text"""
        # Extract order by clauses
        orders = self.intent_classifier.extract_order_by(text, fields)
        
        # Add order by clauses to intent
        for order in orders:
            intent.order_by.append((order["field"], order["direction"]))
        
        # If we have aggregations but no explicit ordering, order by the first aggregation
        if intent.aggregations and not intent.order_by:
            first_agg = intent.aggregations[0]
            agg_field = first_agg.alias or f"{first_agg.operation.value.lower()}_{first_agg.field}"
            intent.order_by.append((agg_field, SortOrder.DESC))
    
    def _extract_limits(self, intent: QueryIntent, text: str) -> None:
        """Extract result limits from the text"""
        limit_info = self.intent_classifier.extract_limit(text)
        if limit_info:
            intent.limit = limit_info["limit"]
        
        # If we have a ranking query type but no limit, set a default limit
        query_type = intent.metadata.get("query_type", "")
        if "ranking" in query_type and intent.limit is None:
            intent.limit = 10  # Default to top 10 for ranking queries
    
    def _apply_context(self, intent: QueryIntent) -> None:
        """Apply context from previous interactions to the current intent"""
        if not self.context:
            return
        
        # Example: Carry over time frame if not specified in current query
        if "time_frame" in self.context and not any(f.field == "תאריך" for f in intent.filters):
            time_frame = self.context["time_frame"]
            if isinstance(time_frame, dict) and "start" in time_frame and "end" in time_frame:
                intent.filters.append(FilterCondition(
                    field="תאריך",
                    operator=ComparisonOperator.BETWEEN,
                    value=(time_frame["start"], time_frame["end"])
                ))
        
        # Example: Carry over filters for the same entity
        if "entity" in self.context and "filters" in self.context:
            entity = self.context["entity"]
            if entity == intent.entities[0] if intent.entities else False:
                for filt in self.context["filters"]:
                    # Only add filter if not already present
                    if not any(f.field == filt["field"] for f in intent.filters):
                        intent.filters.append(FilterCondition(
                            field=filt["field"],
                            operator=ComparisonOperator(filt["operator"]),
                            value=filt["value"]
                        ))
    
    def _validate_intent(self, intent: QueryIntent) -> None:
        """Validate the query intent and make any necessary adjustments"""
        # Ensure we have at least one entity
        if not intent.entities and hasattr(intent, 'target_entity') and intent.target_entity:
            intent.entities = [intent.target_entity]
        
        # If no entities found, use a default
        if not intent.entities:
            intent.entities = ["לקוחות"]  # Default to customers
        
        # Ensure we have at least one aggregation
        if not intent.aggregations:
            intent.aggregations.append(Aggregation(
                field="*",
                operation=AggregationType.COUNT
            ))
        
        # If we have a time dimension in group by but no time filter, add a default one
        time_fields = ["תאריך", "זמן", "שעה", "יום", "חודש", "שנה", "רבעון"]
        has_time_group = any(group in time_fields for group in intent.group_by)
        has_time_filter = any(f.field in time_fields for f in intent.filters)
        
        if has_time_group and not has_time_filter:
            # Default to last 30 days
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            intent.filters.append(FilterCondition(
                field="תאריך",
                operator=ComparisonOperator.GREATER_OR_EQUAL,
                value=start_date
            ))
    
    def _update_context(self, intent: QueryIntent) -> None:
        """Update context based on the current intent"""
        if intent.entities:
            self.context["entity"] = intent.entities[0]
        
        # Store time frame if we have date filters
        date_filters = [f for f in intent.filters if f.field in ["תאריך", "זמן", "שעה"]]
        if date_filters:
            for df in date_filters:
                if df.operator == ComparisonOperator.BETWEEN and isinstance(df.value, (list, tuple)):
                    self.context["time_frame"] = {
                        "start": df.value[0],
                        "end": df.value[1]
                    }
                    break
                elif df.operator in [ComparisonOperator.GREATER_OR_EQUAL, 
                                   ComparisonOperator.GREATER_THAN]:
                    self.context["time_frame"] = {
                        "start": df.value,
                        "end": None
                    }
                    break
        
        # Store filters for potential follow-up questions
        self.context["filters"] = [
            {
                "field": f.field,
                "operator": f.operator.value,
                "value": f.value
            }
            for f in intent.filters
        ]
    
    def clear_context(self) -> None:
        """Clear the current conversation context"""
        self.context = {}
    
    def get_sql(self, intent: QueryIntent) -> str:
        """
        Generate SQL from a QueryIntent
        
        Args:
            intent: The QueryIntent to convert to SQL
            
        Returns:
            str: The generated SQL query
        """
        # This is a simplified version - in a real implementation, you would
        # use a SQL builder library or ORM to generate the query
        
        # Start with SELECT
        select_parts = []
        
        # Add aggregations
        for agg in intent.aggregations:
            select_parts.append(agg.to_sql())
        
        # Add group by fields
        for field in intent.group_by:
            if field not in select_parts:
                select_parts.append(field)
        
        # Build SELECT clause
        select_clause = "SELECT " + ", \n       ".join(select_parts) if select_parts else "SELECT *"
        
        # Build FROM clause (simplified)
        from_clause = f"\nFROM {intent.entities[0] if intent.entities else 'customers'}"
        
        # Build WHERE clause
        where_parts = []
        for filt in intent.filters:
            where_parts.append(filt.to_sql())
        
        where_clause = "\nWHERE " + "\n  AND ".join(where_parts) if where_parts else ""
        
        # Build GROUP BY clause
        group_by_clause = "\nGROUP BY " + ", ".join(intent.group_by) if intent.group_by else ""
        
        # Build ORDER BY clause
        order_by_parts = []
        for field, direction in intent.order_by:
            order_by_parts.append(f"{field} {direction.value}")
        
        order_by_clause = "\nORDER BY " + ", ".join(order_by_parts) if order_by_parts else ""
        
        # Build LIMIT clause
        limit_clause = f"\nLIMIT {intent.limit}" if intent.limit is not None else ""
        
        # Combine all clauses
        sql = (
            f"{select_clause}"
            f"{from_clause}"
            f"{where_clause}"
            f"{group_by_clause}"
            f"{order_by_clause}"
            f"{limit_clause};"
        )
        
        return sql

