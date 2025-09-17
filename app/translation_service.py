from dataclasses import dataclass
from typing import Dict, List, Optional


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
    def __init__(self):
        self._by_canonical: Dict[str, Mapping] = {}
        self._alias_index: Dict[str, str] = {}

        # Define the dictionary mappings
        seed: List[Mapping] = [
            Mapping(
                canonical_term="לקוחות",
                table="customer",
                field="id",
                default_agg="COUNT",
                date_field="created_at",
                aliases=[
                    "לקוחות חדשים", "מספר לקוחות", "כמות לקוחות", 
                    "אנשים", "משתמשים", "צרכנים", "מנויים"
                ]
            ),
            Mapping(
                canonical_term="עיר",
                table="customer",
                field="city",
                aliases=["ערים", "יישוב", "מקום מגורים", "ישוב"]
            ),
            Mapping(
                canonical_term="שם",
                table="customer",
                field="name",
                aliases=["שם מלא", "שם פרטי", "שם משפחה"]
            ),
            Mapping(
                canonical_term="תאריך יצירה",
                table="customer",
                field="created_at",
                aliases=["נרשם בתאריך", "תאריך רישום", "מועד הרשמה", "תאריך הצטרפות"]
            ),
            # Add more entities as needed
            Mapping(
                canonical_term="סניף",
                table="customer",
                field="branch",
                aliases=["סניפים", "סניף מגורים"]
            )
        ]

        # Index the mappings
        for m in seed:
            key = _normalize_hebrew(m.canonical_term)
            self._by_canonical[key] = m
            if m.aliases:
                for alias in m.aliases:
                    akey = _normalize_hebrew(alias)
                    self._alias_index[akey] = key

    def has(self, term: str) -> bool:
        """Check if a term exists in the dictionary"""
        n = _normalize_hebrew(term)
        return n in self._by_canonical or n in self._alias_index

    def resolve(self, term: str) -> Mapping:
        """Resolve a term to its canonical mapping"""
        n = _normalize_hebrew(term)
        if n in self._by_canonical:
            return self._by_canonical[n]
        if n in self._alias_index:
            canonical = self._alias_index[n]
            return self._by_canonical[canonical]
        raise TermNotFoundError(f"Term not found: '{term}'")
