"""
Enhanced Schema Loader for Multi-Source BI Layer

This module loads and validates schema definitions from YAML files
and provides an interface for accessing multi-source schema information.

Features:
- Multi-source data source support
- Business glossary and terminology mapping
- Analytics configuration (measures/dimensions)
- Enhanced validation and error handling

Version: 2.0
"""

from typing import Dict, Any, List, Optional, Tuple, Set
import yaml
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class SchemaValidationError(Exception):
    """Raised when schema validation fails"""
    pass

class EntityNotFoundError(Exception):
    """Raised when requested entity is not found"""
    pass

class EnhancedSchemaLoader:
    """Enhanced schema loader for multi-source BI environments"""
    
    def __init__(self, schema_path: str = "schema/registry.yaml"):
        """
        Initialize enhanced schema loader.
        
        Args:
            schema_path: Path to schema registry YAML file
        """
        self.schema_path = Path(schema_path)
        self.schema: Dict[str, Any] = {}
        self.data_sources: Dict[str, Any] = {}
        self.business_model: Dict[str, Any] = {}
        self.business_glossary: Dict[str, Any] = {}
        self.analytics_config: Dict[str, Any] = {}
        
        self._load_schema()
        
    def _load_schema(self) -> None:
        """Load and parse schema from YAML file"""
        try:
            with open(self.schema_path, 'r', encoding='utf-8') as f:
                self.schema = yaml.safe_load(f)
            
            # Extract major sections
            self.data_sources = self.schema.get('data_sources', {})
            self.business_model = self.schema.get('business_model', {})
            self.business_glossary = self.schema.get('business_glossary', {})
            self.analytics_config = self.schema.get('analytics_config', {})
            
            self._validate_schema()
            logger.info(f"Successfully loaded enhanced schema from {self.schema_path}")
            logger.info(f"Found {len(self.get_entity_names())} entities and {len(self.data_sources)} data sources")
            
        except Exception as e:
            logger.error(f"Failed to load schema: {str(e)}")
            raise SchemaValidationError(f"Schema loading failed: {str(e)}")
            
    def _validate_schema(self) -> None:
        """Validate loaded schema structure for new format"""
        # Check version
        version = self.schema.get('version')
        if not version or float(version) < 2.0:
            logger.warning(f"Schema version {version} may not support all features. Recommend version 2.0+")
        
        # Validate data sources
        if not self.data_sources:
            raise SchemaValidationError("Schema must define at least one data source")
        
        # Check default data source exists
        default_source = self.schema.get('settings', {}).get('default_source')
        if default_source and default_source not in self.data_sources:
            raise SchemaValidationError(f"Default data source '{default_source}' not found in data_sources")
        
        # Validate business model
        if not self.business_model or 'entities' not in self.business_model:
            raise SchemaValidationError("Schema must define business_model with entities")
        
        # Validate each entity
        for entity_name, entity_def in self.business_model['entities'].items():
            self._validate_entity_definition(entity_name, entity_def)
            
    def _validate_entity_definition(self, entity_name: str, entity_def: Dict[str, Any]) -> None:
        """
        Validate entity definition structure.
        
        Args:
            entity_name: Name of the entity
            entity_def: Entity definition dictionary
        """
        required_keys = {'physical_table', 'fields'}
        if not all(key in entity_def for key in required_keys):
            raise SchemaValidationError(
                f"Entity '{entity_name}' missing required keys: {required_keys - entity_def.keys()}"
            )
            
        # Validate data source reference
        data_source = entity_def.get('data_source')
        if data_source and data_source not in self.data_sources:
            raise SchemaValidationError(
                f"Entity '{entity_name}' references unknown data source: {data_source}"
            )
            
        # Validate fields
        for field_name, field_def in entity_def['fields'].items():
            self._validate_field_definition(entity_name, field_name, field_def)
            
    def _validate_field_definition(self, entity_name: str, field_name: str, 
                                 field_def: Dict[str, Any]) -> None:
        """
        Validate field definition structure.
        
        Args:
            entity_name: Name of the entity
            field_name: Name of the field
            field_def: Field definition dictionary
        """
        required_keys = {'physical_column', 'type'}
        if not all(key in field_def for key in required_keys):
            raise SchemaValidationError(
                f"Field '{field_name}' in entity '{entity_name}' missing required keys: "
                f"{required_keys - field_def.keys()}"
            )
            
        # Validate field type
        valid_types = {'integer', 'string', 'decimal', 'datetime', 'boolean'}
        field_type = field_def.get('type')
        if field_type not in valid_types:
            logger.warning(f"Field '{field_name}' has unknown type '{field_type}'. Valid types: {valid_types}")
            
    # === Entity Management ===
    def get_entity_names(self) -> List[str]:
        """Get list of all entity names defined in schema"""
        return list(self.business_model.get('entities', {}).keys())
        
    def get_entity_definition(self, entity_name: str) -> Dict[str, Any]:
        """
        Get complete definition for an entity.
        
        Args:
            entity_name: Name of the entity
            
        Returns:
            Entity definition dictionary
        """
        entities = self.business_model.get('entities', {})
        if entity_name not in entities:
            raise EntityNotFoundError(f"Entity '{entity_name}' not found in schema")
        return entities[entity_name]
    
    def get_physical_table_name(self, entity_name: str) -> str:
        """
        Get physical table name for an entity.
        
        Args:
            entity_name: Name of the entity
            
        Returns:
            Physical table name in the database
        """
        entity_def = self.get_entity_definition(entity_name)
        return entity_def['physical_table']
    
    def get_entity_data_source(self, entity_name: str) -> str:
        """
        Get data source ID for an entity.
        
        Args:
            entity_name: Name of the entity
            
        Returns:
            Data source ID
        """
        entity_def = self.get_entity_definition(entity_name)
        return entity_def.get('data_source', self.schema.get('settings', {}).get('default_source', 'default'))
        
    # === Field Management ===
    def get_field_names(self, entity_name: str) -> List[str]:
        """
        Get list of field names for an entity.
        
        Args:
            entity_name: Name of the entity
            
        Returns:
            List of field names
        """
        entity_def = self.get_entity_definition(entity_name)
        return list(entity_def['fields'].keys())
        
    def get_field_definition(self, entity_name: str, field_name: str) -> Dict[str, Any]:
        """
        Get complete definition for a field.
        
        Args:
            entity_name: Name of the entity
            field_name: Name of the field
            
        Returns:
            Field definition dictionary
        """
        entity_def = self.get_entity_definition(entity_name)
        if field_name not in entity_def['fields']:
            raise ValueError(f"Field '{field_name}' not found in entity '{entity_name}'")
        return entity_def['fields'][field_name]
    
    def get_physical_column_name(self, entity_name: str, field_name: str) -> str:
        """
        Get physical column name for a field.
        
        Args:
            entity_name: Entity name
            field_name: Field name
            
        Returns:
            Physical column name in the database
        """
        field_def = self.get_field_definition(entity_name, field_name)
        return field_def['physical_column']
        
    # === Relationships ===
    def get_relationships(self, entity_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get relationships defined in schema.
        
        Args:
            entity_name: Filter relationships by entity name (optional)
            
        Returns:
            List of relationship definitions
        """
        relationships = self.business_model.get('relationships', {})
        if entity_name:
            # Filter relationships where this entity is involved
            filtered = {}
            for rel_name, rel_def in relationships.items():
                if (rel_def.get('from_entity') == entity_name or 
                    rel_def.get('to_entity') == entity_name):
                    filtered[rel_name] = rel_def
            return list(filtered.values())
        return list(relationships.values())
    
    # === Data Sources ===
    def get_data_source_definition(self, source_id: str) -> Dict[str, Any]:
        """
        Get data source definition.
        
        Args:
            source_id: ID of the data source
            
        Returns:
            Data source definition
        """
        if source_id not in self.data_sources:
            raise ValueError(f"Data source '{source_id}' not found")
        return self.data_sources[source_id]
    
    def get_connection_string(self, source_id: str) -> str:
        """
        Get connection string for a data source (with environment variable resolution).
        
        Args:
            source_id: ID of the data source
            
        Returns:
            Resolved connection string
        """
        source_def = self.get_data_source_definition(source_id)
        connection_string = source_def.get('connection_string', '')
        
        # Simple environment variable resolution
        import re
        def replace_env(match):
            env_var = match.group(1)
            default_val = match.group(2) if match.group(2) else ''
            return os.getenv(env_var, default_val)
        
        # Replace ${VAR:-default} pattern
        resolved = re.sub(r'\$\{([^:}]+)(?::-([^}]*))?\}', replace_env, connection_string)
        return resolved
    
    # === Business Glossary ===
    def search_business_terms(self, hebrew_term: str) -> List[Dict[str, Any]]:
        """
        Search for entity references that match a Hebrew business term.
        
        Args:
            hebrew_term: Hebrew term to search for
            
        Returns:
            List of matching term definitions with entity references
        """
        matches = []
        for category_name, terms in self.business_glossary.items():
            for term_def in terms:
                hebrew_terms = term_def.get('hebrew_terms', [])
                if hebrew_term.lower() in [t.lower() for t in hebrew_terms]:
                    matches.append(term_def)
        return matches
    
    def get_entity_for_term(self, hebrew_term: str) -> Optional[Tuple[str, str]]:
        """
        Get best matching entity and field for a Hebrew term.
        
        Args:
            hebrew_term: Hebrew business term
            
        Returns:
            Tuple of (entity_name, field_name) or None if not found
        """
        matches = self.search_business_terms(hebrew_term)
        if not matches:
            return None
        
        # Get the highest confidence match
        best_match = max(matches, key=lambda x: x.get('confidence', 0.0))
        entity_ref = best_match.get('entity_ref', '')
        
        if '.' in entity_ref:
            entity_name, field_name = entity_ref.split('.', 1)
            return (entity_name, field_name)
        
        return None

    # === Analytics Configuration ===
    def get_measures(self) -> Dict[str, Any]:
        """Get all available measures for analytics"""
        return self.analytics_config.get('measures', {})
    
    def get_dimensions(self) -> Dict[str, Any]:
        """Get all available dimensions for analytics"""
        return self.analytics_config.get('dimensions', {})
    
    def get_query_templates(self) -> Dict[str, Any]:
        """Get predefined query templates"""
        return self.schema.get('query_templates', {})
    
    # === Utility Methods ===
    def get_fact_tables(self) -> List[str]:
        """Get list of entities marked as fact tables"""
        fact_entities = []
        for entity_name, entity_def in self.business_model.get('entities', {}).items():
            if entity_def.get('is_fact_table', False):
                fact_entities.append(entity_name)
        return fact_entities
    
    def get_dimension_tables(self) -> List[str]:
        """Get list of entities that are dimension tables (not fact tables)"""
        all_entities = self.get_entity_names()
        fact_entities = self.get_fact_tables()
        return [e for e in all_entities if e not in fact_entities]
    
    def generate_sql_select_template(self, entity_name: str) -> str:
        """
        Generate a basic SQL SELECT template for an entity.
        
        Args:
            entity_name: Name of the entity
            
        Returns:
            SQL SELECT statement template
        """
        entity_def = self.get_entity_definition(entity_name)
        table_name = entity_def['physical_table']
        
        # Build field list with aliases
        field_parts = []
        for field_name, field_def in entity_def['fields'].items():
            physical_col = field_def['physical_column']
            if physical_col != field_name:
                field_parts.append(f"{physical_col} AS {field_name}")
            else:
                field_parts.append(field_name)
        
        fields_sql = ",\n    ".join(field_parts)
        return f"SELECT\n    {fields_sql}\nFROM {table_name}"


# Legacy compatibility class (backwards compatibility)
class SchemaLoader(EnhancedSchemaLoader):
    """Backwards compatible schema loader"""
    def __init__(self, schema_path: str = "schema/registry.yaml"):
        super().__init__(schema_path)
        
    def get_table_names(self) -> List[str]:
        """Legacy method - redirects to get_entity_names"""
        return self.get_entity_names()
    
    def get_table_definition(self, table_name: str) -> Dict[str, Any]:
        """Legacy method - redirects to get_entity_definition"""
        return self.get_entity_definition(table_name)


# Create global enhanced schema loader instance
try:
    schema_loader = EnhancedSchemaLoader()
    logger.info("Enhanced schema loader initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize schema loader: {str(e)}")
    # Create a dummy loader to prevent import errors
    class DummySchemaLoader:
        def __getattr__(self, name):
            raise RuntimeError(f"Schema loader failed to initialize: {str(e)}")
    schema_loader = DummySchemaLoader()