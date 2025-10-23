"""
Hebrew Query Parser
Converts Hebrew text queries into AST representation
Uses YAML configuration for entity and attribute recognition
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass

from .ast_nodes import (
    ParsedQuery, SelectQuery, ShortcutQuery, EntityRef, AttributeRef,
    FilterCondition, AggregateFunction, SortClause,
    AggregationType, FilterOperator, SortDirection,
    create_entity_ref, create_attribute_ref, create_filter, create_aggregate, create_sort
)
from app.config_loader import config_loader
from app.config_models import Ontology, Functions, Datasource, Mappings

logger = logging.getLogger(__name__)

@dataclass
class MatchedTerm:
    """Represents a matched Hebrew term"""
    hebrew_term: str
    entity: Optional[str] = None
    attribute: Optional[str] = None
    aggregation: Optional[str] = None
    position: int = 0
    length: int = 0

class HebrewQueryParser:
    """Parses Hebrew queries into AST representation"""
    
    def __init__(self, client_id: str = "sample-client"):
        self.client_id = client_id
        self._ontology: Optional[Ontology] = None
        self._functions: Optional[Functions] = None
        self._datasource: Optional[Datasource] = None
        self._mappings: Optional[Mappings] = None
        
        # Cached lookups for performance
        self._hebrew_to_entity: Optional[Dict[str, str]] = None
        self._hebrew_to_attribute: Optional[Dict[str, Tuple[str, str]]] = None
        self._hebrew_to_aggregation: Optional[Dict[str, str]] = None
        
    def _load_config(self):
        """Load configuration if not already loaded"""
        if self._ontology is None:
            self._ontology = config_loader.load_shared_ontology()
            self._functions = config_loader.load_shared_functions()
            self._datasource, self._mappings = config_loader.load_client_config(self.client_id)
            self._build_lookup_tables()
    
    def _build_lookup_tables(self):
        """Build Hebrew term lookup tables for fast matching"""
        self._hebrew_to_entity = {}
        self._hebrew_to_attribute = {}
        self._hebrew_to_aggregation = {}
        
        # Build entity lookups
        for entity_name, entity in self._ontology.entities.items():
            for hebrew_name in entity.hebrew_names:
                self._hebrew_to_entity[hebrew_name.lower()] = entity_name
                
            # Add client-specific entity terms
            if (self._mappings.custom_terms and 
                self._mappings.custom_terms.entities and
                entity_name in self._mappings.custom_terms.entities):
                
                custom_entity = self._mappings.custom_terms.entities[entity_name]
                for hebrew_name in custom_entity.additional_names:
                    self._hebrew_to_entity[hebrew_name.lower()] = entity_name
        
        # Build attribute lookups
        for entity_name, entity in self._ontology.entities.items():
            for attr_name, attr in entity.attributes.items():
                for hebrew_name in attr.hebrew_names:
                    self._hebrew_to_attribute[hebrew_name.lower()] = (entity_name, attr_name)
                    
                # Add client-specific attribute terms
                if (self._mappings.custom_terms and 
                    self._mappings.custom_terms.attributes and
                    attr_name in self._mappings.custom_terms.attributes):
                    
                    custom_attr = self._mappings.custom_terms.attributes[attr_name]
                    for hebrew_name in custom_attr.additional_names:
                        self._hebrew_to_attribute[hebrew_name.lower()] = (entity_name, attr_name)
        
        # Build aggregation lookups
        for agg_name, agg in self._functions.aggregations.items():
            for hebrew_name in agg.hebrew_names:
                self._hebrew_to_aggregation[hebrew_name.lower()] = agg_name
                
        logger.debug(f"Built lookup tables: {len(self._hebrew_to_entity)} entities, "
                    f"{len(self._hebrew_to_attribute)} attributes, {len(self._hebrew_to_aggregation)} aggregations")
    
    def _find_matched_terms(self, query_text: str) -> List[MatchedTerm]:
        """Find all matched Hebrew terms in query text"""
        query_lower = query_text.lower()
        matches = []
        
        # Find entity matches
        for hebrew_term, entity_name in self._hebrew_to_entity.items():
            if hebrew_term in query_lower:
                start_pos = query_lower.find(hebrew_term)
                matches.append(MatchedTerm(
                    hebrew_term=hebrew_term,
                    entity=entity_name,
                    position=start_pos,
                    length=len(hebrew_term)
                ))
        
        # Find attribute matches
        for hebrew_term, (entity_name, attr_name) in self._hebrew_to_attribute.items():
            if hebrew_term in query_lower:
                start_pos = query_lower.find(hebrew_term)
                matches.append(MatchedTerm(
                    hebrew_term=hebrew_term,
                    entity=entity_name,
                    attribute=attr_name,
                    position=start_pos,
                    length=len(hebrew_term)
                ))
        
        # Find aggregation matches
        for hebrew_term, agg_name in self._hebrew_to_aggregation.items():
            if hebrew_term in query_lower:
                start_pos = query_lower.find(hebrew_term)
                matches.append(MatchedTerm(
                    hebrew_term=hebrew_term,
                    aggregation=agg_name,
                    position=start_pos,
                    length=len(hebrew_term)
                ))
        
        # Sort by position for consistent processing
        matches.sort(key=lambda m: m.position)
        return matches
    
    def _check_shortcuts(self, query_text: str) -> Optional[ShortcutQuery]:
        """Check if query matches any predefined shortcuts"""
        if not self._mappings.shortcuts:
            return None
            
        query_lower = query_text.lower()
        
        for shortcut_name, shortcut in self._mappings.shortcuts.items():
            if shortcut_name in query_lower:
                return ShortcutQuery(
                    shortcut_name=shortcut_name,
                    sql=shortcut.sql,
                    description=shortcut.description,
                    parameters=shortcut.parameters or {}
                )
        
        return None
    
    def _determine_intent(self, matches: List[MatchedTerm], query_text: str) -> str:
        """Determine query intent from matched terms and text patterns"""
        query_lower = query_text.lower()
        
        # Check for aggregation intent
        agg_matches = [m for m in matches if m.aggregation]
        if agg_matches:
            return "aggregate"
        
        # Check for common Hebrew patterns
        if any(word in query_lower for word in ["הצג", "הראה", "תציג"]):
            return "select"
        
        if any(word in query_lower for word in ["כמה", "מספר"]):
            return "count"
        
        if any(word in query_lower for word in ["סכום", "סיכום", "חיבור"]):
            return "sum"
        
        if any(word in query_lower for word in ["ב", "של", "עם"]):
            return "filter"
        
        # Default intent
        return "select"
    
    def _build_ast_from_matches(self, matches: List[MatchedTerm], query_text: str, intent: str) -> SelectQuery:
        """Build AST from matched terms and intent"""
        
        # Collect unique entities
        entity_names = list(set(m.entity for m in matches if m.entity))
        entities = [create_entity_ref(name) for name in entity_names]
        
        # Collect attributes
        attributes = []
        for match in matches:
            if match.entity and match.attribute:
                attr_ref = create_attribute_ref(match.entity, match.attribute)
                if attr_ref not in attributes:
                    attributes.append(attr_ref)
        
        # Collect aggregations
        aggregates = []
        for match in matches:
            if match.aggregation:
                agg_type = AggregationType(self._functions.aggregations[match.aggregation].sql_function)
                
                # Find related attribute for aggregation
                attr_matches = [m for m in matches if m.entity and m.attribute and m != match]
                if attr_matches and agg_type in [AggregationType.SUM, AggregationType.AVG, AggregationType.MAX, AggregationType.MIN]:
                    # Use first attribute found
                    attr_match = attr_matches[0]
                    agg_func = create_aggregate(agg_type, attr_match.entity, attr_match.attribute)
                else:
                    # COUNT(*) or general aggregation
                    agg_func = create_aggregate(agg_type)
                    
                aggregates.append(agg_func)
        
        # Build query based on intent
        query = SelectQuery(entities=entities)
        
        if intent == "aggregate" and aggregates:
            query.aggregates = aggregates
            # Don't select attributes when aggregating
            query.attributes = []
        elif intent == "count":
            # Force COUNT aggregation
            query.aggregates = [create_aggregate(AggregationType.COUNT)]
            query.attributes = []
        elif intent == "sum" and attributes:
            # Force SUM on first numeric attribute
            numeric_attrs = [attr for attr in attributes 
                           if self._ontology.entities[attr.entity].attributes[attr.attribute].type in ["integer", "decimal"]]
            if numeric_attrs:
                query.aggregates = [create_aggregate(AggregationType.SUM, numeric_attrs[0].entity, numeric_attrs[0].attribute)]
                query.attributes = []
        else:
            # Regular SELECT
            query.attributes = attributes if attributes else []  # Empty means SELECT *
        
        # Add default limit
        if self._datasource.database_settings.max_results:
            query.limit = self._datasource.database_settings.max_results
        
        return query
    
    def parse(self, query_text: str) -> ParsedQuery:
        """
        Parse Hebrew query text into AST representation
        
        Args:
            query_text: Hebrew query string
            
        Returns:
            ParsedQuery with AST representation
        """
        self._load_config()
        
        # Check for shortcuts first
        shortcut_query = self._check_shortcuts(query_text)
        if shortcut_query:
            return ParsedQuery(
                original_text=query_text,
                query_node=shortcut_query,
                matched_terms=[shortcut_query.shortcut_name],
                confidence=1.0,
                intent="shortcut"
            )
        
        # Find matched terms
        matches = self._find_matched_terms(query_text)
        
        if not matches:
            # No matches found - create empty query
            logger.warning(f"No matches found for query: {query_text}")
            return ParsedQuery(
                original_text=query_text,
                query_node=SelectQuery(entities=[]),
                matched_terms=[],
                confidence=0.0,
                intent="unknown"
            )
        
        # Determine intent
        intent = self._determine_intent(matches, query_text)
        
        # Build AST
        ast_query = self._build_ast_from_matches(matches, query_text, intent)
        
        # Calculate confidence based on term coverage
        matched_terms = [m.hebrew_term for m in matches]
        confidence = min(1.0, len(set(matched_terms)) / max(1, len(query_text.split())))
        
        return ParsedQuery(
            original_text=query_text,
            query_node=ast_query,
            matched_terms=matched_terms,
            confidence=confidence,
            intent=intent
        )