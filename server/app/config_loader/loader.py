"""
YAML Configuration Loader
Dynamically loads and validates all YAML configuration files
Replaces static ORM models with runtime configuration
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Optional, Any
from functools import lru_cache

from app.config_models import Ontology, Functions, Datasource, Mappings

logger = logging.getLogger(__name__)

class ConfigurationError(Exception):
    """Raised when configuration loading or validation fails"""
    pass

class ConfigLoader:
    """Loads and manages YAML-based configuration"""
    
    def __init__(self, config_root: str = "configs"):
        """
        Initialize config loader
        
        Args:
            config_root: Root directory for configuration files
        """
        # Convert to absolute path relative to this file's location
        if not Path(config_root).is_absolute():
            # Get the server directory (2 levels up from this file)
            server_dir = Path(__file__).parent.parent.parent
            self.config_root = server_dir / config_root
        else:
            self.config_root = Path(config_root)
            
        self._ontology: Optional[Ontology] = None
        self._functions: Optional[Functions] = None
        self._client_configs: Dict[str, tuple] = {}  # client_id -> (datasource, mappings)
        
        # Validate config directory exists
        if not self.config_root.exists():
            raise ConfigurationError(f"Configuration directory not found: {self.config_root}")

        self._meta_schema_path = self.config_root / "schemas" / "META_SCHEMA.yaml"
            
    @lru_cache(maxsize=1)
    def load_shared_ontology(self) -> Ontology:
        """Load shared business ontology"""
        if self._ontology is None:
            ontology_path = self.config_root / "shared" / "ontology.yaml"
            
            if not ontology_path.exists():
                raise ConfigurationError(f"Ontology file not found: {ontology_path}")
                
            try:
                with open(ontology_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    
                self._ontology = Ontology(**data)
                logger.info(f"Loaded ontology with {len(self._ontology.entities)} entities")
                
            except yaml.YAMLError as e:
                raise ConfigurationError(f"Invalid YAML in ontology file: {e}")
            except Exception as e:
                raise ConfigurationError(f"Failed to validate ontology: {e}")
                
        return self._ontology
    
    @lru_cache(maxsize=1)
    def load_shared_functions(self) -> Functions:
        """Load shared functions and aggregations"""
        if self._functions is None:
            functions_path = self.config_root / "shared" / "functions.yaml"
            
            if not functions_path.exists():
                raise ConfigurationError(f"Functions file not found: {functions_path}")
                
            try:
                with open(functions_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    
                self._functions = Functions(**data)
                logger.info(f"Loaded functions with {len(self._functions.aggregations)} aggregations")
                
            except yaml.YAMLError as e:
                raise ConfigurationError(f"Invalid YAML in functions file: {e}")
            except Exception as e:
                raise ConfigurationError(f"Failed to validate functions: {e}")
                
        return self._functions
    
    def load_client_config(self, client_id: str) -> tuple[Datasource, Mappings]:
        """
        Load client-specific configuration
        
        Args:
            client_id: Client identifier
            
        Returns:
            Tuple of (datasource, mappings) configurations
        """
        if client_id in self._client_configs:
            return self._client_configs[client_id]
            
        client_dir = self.config_root / "clients" / client_id
        
        if not client_dir.exists():
            raise ConfigurationError(f"Client configuration directory not found: {client_dir}")
            
        # Load datasource configuration
        datasource_path = client_dir / "datasource.yaml"
        if not datasource_path.exists():
            raise ConfigurationError(f"Datasource file not found: {datasource_path}")
            
        try:
            with open(datasource_path, 'r', encoding='utf-8') as f:
                datasource_data = yaml.safe_load(f)
            datasource = Datasource(**datasource_data)
            
        except (yaml.YAMLError, Exception) as e:
            raise ConfigurationError(f"Failed to load datasource config for {client_id}: {e}")
        
        # Load mappings configuration  
        mappings_path = client_dir / "mappings.yaml"
        if not mappings_path.exists():
            raise ConfigurationError(f"Mappings file not found: {mappings_path}")
            
        try:
            with open(mappings_path, 'r', encoding='utf-8') as f:
                mappings_data = yaml.safe_load(f)
            mappings = Mappings(**mappings_data)
            
        except (yaml.YAMLError, Exception) as e:
            raise ConfigurationError(f"Failed to load mappings config for {client_id}: {e}")
        
        # Cache the configurations
        self._client_configs[client_id] = (datasource, mappings)
        
        logger.info(f"Loaded configuration for client: {client_id}")
        return datasource, mappings

    def load_meta_schema(self) -> Dict[str, Any]:
        """Load metadata-driven schema representation from generated YAML."""
        path = self._meta_schema_path

        if not path.exists():
            raise ConfigurationError(f"Meta schema file not found: {path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in meta schema file: {e}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load meta schema file: {e}")

        if not isinstance(data, dict):
            raise ConfigurationError("Meta schema YAML must contain a mapping at the root")

        logger.info(
            "Loaded meta schema YAML with %d tables",
            len((data.get("tables") or {}).keys()),
        )
        return data

# Global config loader instance
config_loader = ConfigLoader()

