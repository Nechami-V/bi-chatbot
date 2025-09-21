from dataclasses import dataclass
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.translation_dictionary import TranslationDictionaryModel


class TermNotFoundError(Exception):
    pass


class AmbiguousTermError(Exception):
    pass


@dataclass(frozen=True)
class Mapping:
    canonical_term: str
    table: str
    field: str
    default_agg: Optional[str] = None
    date_field: Optional[str] = None
    aliases: Optional[List[str]] = None


def _normalize_hebrew(text: str) -> str:
    """Normalize Hebrew text for consistent matching"""
    if text is None:
        return ""
    t = " ".join(text.strip().split())  # Remove extra spaces
    t = t.lower()
    if t.startswith("ה") and len(t) > 1:  # Remove Hebrew definite article
        t = t[1:]
    # Replace final letters with regular letters
    finals = {"ך": "כ", "ם": "מ", "ן": "נ", 
              "ף": "פ", "ץ": "צ"}
    t = "".join(finals.get(ch, ch) for ch in t)
    return t


class TranslationDictionary:
    """Database-backed translation dictionary service"""
    
    def __init__(self, client_id: int = 1, db: Optional[Session] = None):
        self.client_id = client_id
        self._db = db
        self._cache: Dict[str, Mapping] = {}
        self._cache_loaded = False

    def _get_db(self) -> Session:
        """Get database session"""
        if self._db:
            return self._db
        return SessionLocal()

    def _load_cache(self):
        """Load mappings from database into cache"""
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
            print(f"📚 Loaded {len(self._cache)} translation mappings from database")
            
        finally:
            if not self._db:  # Only close if we created the session
                db.close()

    def has(self, term: str) -> bool:
        """Check if a term exists in the dictionary"""
        self._load_cache()
        normalized = _normalize_hebrew(term)
        return normalized in self._cache

    def resolve(self, term: str) -> Mapping:
        """Resolve a term to its canonical mapping"""
        self._load_cache()
        normalized = _normalize_hebrew(term)
        
        if normalized in self._cache:
            return self._cache[normalized]
            
        # Try fuzzy matching
        from rapidfuzz import fuzz
        best_match = None
        best_score = 0
        threshold = 80  # Minimum similarity score
        
        for cached_term, mapping in self._cache.items():
            score = fuzz.ratio(normalized, cached_term)
            if score > best_score and score >= threshold:
                best_score = score
                best_match = mapping
                
        if best_match:
            print(f"🔍 Fuzzy matched '{term}' to '{best_match.canonical_term}' (score: {best_score})")
            return best_match
            
        raise TermNotFoundError(f"Term '{term}' not found in translation dictionary")

    def add_mapping(self, user_term: str, db_table: str, db_field: str, 
                   default_agg: Optional[str] = None, date_field: Optional[str] = None) -> bool:
        """Add a new mapping to the dictionary"""
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
        """Get all mappings for this client"""
        self._load_cache()
        return list(self._cache.values())

    def refresh_cache(self):
        """Force refresh of the cache from database"""
        self._cache_loaded = False
        self._cache.clear()
        self._load_cache()


# For backward compatibility with existing code
def get_default_dictionary() -> TranslationDictionary:
    """Get a default translation dictionary instance"""
    return TranslationDictionary(client_id=1)