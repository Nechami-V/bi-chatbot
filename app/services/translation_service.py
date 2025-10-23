"""
Translation Service - Hebrew Business Terms to Database Field Mapping

This service provides translation capabilities between Hebrew business terms
and database table/field names, enabling natural language understanding
for business intelligence queries.

Key Features:
- Database-backed translation mappings
- Hebrew text normalization and fuzzy matching
- Client-specific term dictionaries
- Caching for performance optimization

Author: BI Chatbot Team
Version: 2.0.0
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.translation_dictionary import TranslationDictionaryModel

# Configure logger
logger = logging.getLogger(__name__)


class TermNotFoundError(Exception):
    """Raised when a Hebrew business term cannot be found in the dictionary"""
    pass


class AmbiguousTermError(Exception):
    """Raised when a Hebrew term matches multiple database mappings"""
    pass


@dataclass(frozen=True)
class Mapping:
    """
    Represents a mapping between Hebrew business term and database field
    
    Attributes:
        canonical_term: The standard Hebrew business term
        table: Database table name where the data resides
        field: Database field/column name
        default_agg: Default aggregation function (COUNT, SUM, AVG, etc.)
        date_field: Related date field for time-based queries
        aliases: Alternative terms that map to the same field
    """
    canonical_term: str
    table: str
    field: str
    default_agg: Optional[str] = None
    date_field: Optional[str] = None
    aliases: Optional[List[str]] = None


def _normalize_hebrew(text: Optional[str]) -> str:
    """Normalize Hebrew text for consistent matching."""

    if not text:
        return ""

    normalized = " ".join(text.strip().split()).lower()

    # Remove the Hebrew definite article prefix when applicable
    if normalized.startswith("ה") and len(normalized) > 1:
        normalized = normalized[1:]

    # Replace Hebrew final letters with their standard forms
    final_letter_map = {
        "ך": "כ",
        "ם": "מ",
        "ן": "נ",
        "ף": "פ",
        "ץ": "צ",
    }
    return "".join(final_letter_map.get(char, char) for char in normalized)


class TranslationDictionary:
    """Database-backed translation dictionary service."""

    def __init__(self, client_id: int = 1, db: Optional[Session] = None) -> None:
        self.client_id = client_id
        self._db = db
        self._cache: Dict[str, Mapping] = {}
        self._cache_loaded = False

    def _get_db(self) -> Session:
        """Return an active SQLAlchemy session, creating one if required."""
        if self._db:
            return self._db
        return SessionLocal()

    def _load_cache(self) -> None:
        """Load translation mappings from the database into the local cache."""
        if self._cache_loaded:
            return
            
        db = self._get_db()
        try:
            # Get all mappings for this client
            db_mappings = db.query(TranslationDictionaryModel).filter(
                TranslationDictionaryModel.client_id == self.client_id
            ).all()
            
            for db_mapping in db_mappings:
                normalized_term = _normalize_hebrew(db_mapping.user_term)
                mapping = Mapping(
                    canonical_term=db_mapping.user_term,
                    table=db_mapping.db_table,
                    field=db_mapping.db_field,
                    default_agg=db_mapping.default_agg,
                    date_field=db_mapping.date_field
                )
                self._cache[normalized_term] = mapping
                
            self._cache_loaded = True
            logger.info(f"Loaded {len(self._cache)} translation mappings from database")
            
        finally:
            if not self._db:  # Only close if we created the session
                db.close()

    def has(self, term: str) -> bool:
        """Return True if the given term exists in the dictionary."""
        self._load_cache()
        normalized = _normalize_hebrew(term)
        return normalized in self._cache

    def resolve(self, term: str) -> Mapping:
        """Return the mapping for the supplied term, using fuzzy matching if needed."""
        self._load_cache()
        normalized = _normalize_hebrew(term)
        
        if normalized in self._cache:
            return self._cache[normalized]
            
        try:
            from rapidfuzz import fuzz
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise TermNotFoundError(
                "rapidfuzz package is required for fuzzy matching"
            ) from exc

        best_match: Optional[Mapping] = None
        best_score = 0
        threshold = 80  # Minimum similarity score

        for cached_term, mapping in self._cache.items():
            score = fuzz.ratio(normalized, cached_term)
            if score > best_score and score >= threshold:
                best_score = score
                best_match = mapping

        if best_match:
            logger.info(
                f"Fuzzy matched '{term}' to '{best_match.canonical_term}' (score: {best_score})"
            )
            return best_match
            
        raise TermNotFoundError(f"Term '{term}' not found in translation dictionary")

    def add_mapping(self, user_term: str, db_table: str, db_field: str, 
                   default_agg: Optional[str] = None, date_field: Optional[str] = None) -> bool:
        """Persist a new translation mapping and refresh the in-memory cache."""
        db = self._get_db()
        try:
            # Check if mapping already exists
            existing = db.query(TranslationDictionaryModel).filter(
                TranslationDictionaryModel.client_id == self.client_id,
                TranslationDictionaryModel.user_term == user_term
            ).first()
            
            if existing:
                return False  # Already exists
                
            # Add new mapping
            new_mapping = TranslationDictionaryModel(
                client_id=self.client_id,
                user_term=user_term,
                db_table=db_table,
                db_field=db_field,
                default_agg=default_agg,
                date_field=date_field
            )
            
            db.add(new_mapping)
            db.commit()
            
            # Clear cache to force reload
            self._cache_loaded = False
            self._cache.clear()
            
            return True
            
        finally:
            if not self._db:
                db.close()

    def get_all_mappings(self) -> List[Mapping]:
        """Return a list of all mappings for the configured client."""
        self._load_cache()
        return list(self._cache.values())

    def refresh_cache(self) -> None:
        """Clear and repopulate the local cache from the database."""
        self._cache_loaded = False
        self._cache.clear()
        self._load_cache()


# For backward compatibility with existing code
def get_default_dictionary() -> TranslationDictionary:
    """Return a default translation dictionary instance for client_id=1."""
    return TranslationDictionary(client_id=1)