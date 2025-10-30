"""
Prompt Manager: loads YAML prompt templates per pack and renders them with Jinja2.

Features:
- Packs: subfolders under PROMPTS_DIR (e.g., configs/prompts/pack_default)
- Files per type: answer.yml, sql_export.yml, sql_ratio.yml
- External schema injection: supply a dict, exposed to template as `schema` and `schema_json`
- Variables injection: extra context for templates

Environment/config:
- config.PACK must be set (no default) to select active pack
- config.PROMPTS_DIR base directory for packs (default configs/prompts)
- config.SCHEMAS_DIR base directory for schemas (default configs/schemas)
"""

from pathlib import Path
from typing import Dict, Any, Optional
import json

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from app.simple_config import config


class PromptNotConfigured(Exception):
    pass


class PromptManager:
    SUPPORTED_TYPES = ("answer", "sql_export", "sql_ratio")

    def __init__(self, base_dir: Optional[str] = None, pack: Optional[str] = None):
        self.base_dir = Path(base_dir or config.PROMPTS_DIR)
        self.pack = (pack or config.PACK or "").strip()
        if not self.pack:
            raise PromptNotConfigured("PACK is not set. Please set PACK in environment to select a prompt pack.")

        self.pack_dir = self.base_dir / self.pack
        if not self.pack_dir.exists():
            raise FileNotFoundError(f"Prompt pack folder not found: {self.pack_dir}")

        # Jinja2 environment for YAML templates
        self.env = Environment(
            loader=FileSystemLoader(str(self.pack_dir)),
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
            autoescape=False,
        )
        # Add tojson filter for convenience
        self.env.filters["tojson"] = lambda obj: json.dumps(obj, ensure_ascii=False)

    def render(self, prompt_type: str, schema: Dict[str, Any], variables: Optional[Dict[str, Any]] = None) -> str:
        """Render a prompt template of given type using Jinja2.

        - Loads `<type>.yml` from selected pack
        - Renders template with variables + schema injected as `schema` and `schema_json`
        - The YAML file may contain either a top-level `prompt:` key or be a plain template string
        """
        if prompt_type not in self.SUPPORTED_TYPES:
            raise ValueError(f"Unsupported prompt type: {prompt_type}")

        tpl_name = f"{prompt_type}.yml"
        # Load raw YAML template file as text (for Jinja rendering)
        template = self.env.get_template(tpl_name)

        ctx = dict(variables or {})
        ctx["schema"] = schema
        ctx["schema_json"] = schema  # can be used with |tojson in template

        rendered = template.render(**ctx)

        # After rendering, YAML may wrap the prompt in a key. Try parse; fall back to raw string.
        try:
            data = yaml.safe_load(rendered)
            if isinstance(data, dict) and "prompt" in data:
                return str(data["prompt"]).strip()
        except Exception:
            pass
        return rendered.strip()

    def render_all(self, schema: Dict[str, Any], variables: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        """Render answer, sql_export, sql_ratio prompts and return as dict."""
        out: Dict[str, str] = {}
        for name in self.SUPPORTED_TYPES:
            out[name] = self.render(name, schema=schema, variables=variables)
        return out

