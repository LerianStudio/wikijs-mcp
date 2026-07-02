"""Configuration management for WikiJS MCP Server."""

import os
from pathlib import Path

from pydantic import BaseModel, Field


class WikiJSConfig(BaseModel):
    """Configuration for Wiki.js connection."""

    url: str = Field(default="")
    api_key: str = Field(default="")
    graphql_endpoint: str = Field(default="/graphql")
    debug: bool = Field(default=False)
    templates_enabled: bool = Field(default=True)
    templates_dir: str = Field(default="")

    @classmethod
    def load_config(cls) -> "WikiJSConfig":
        """Load configuration from environment variables."""
        return cls(
            url=os.getenv("WIKIJS_URL", ""),
            api_key=os.getenv("WIKIJS_API_KEY", ""),
            graphql_endpoint=os.getenv("WIKIJS_GRAPHQL_ENDPOINT", "/graphql"),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            templates_enabled=os.getenv("WIKIJS_TEMPLATES_ENABLED", "true").lower()
            not in ("false", "0", "no"),
            templates_dir=os.getenv("WIKIJS_TEMPLATES_DIR", ""),
        )

    @property
    def graphql_url(self) -> str:
        """Get the full GraphQL endpoint URL."""
        return f"{self.url.rstrip('/')}{self.graphql_endpoint}"

    @property
    def headers(self) -> dict[str, str]:
        """Get authentication headers for API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @property
    def resolved_templates_dir(self) -> Path:
        """Resolve the on-disk directory that holds default templates."""
        if self.templates_dir:
            return Path(self.templates_dir)
        # Prefer importlib.resources so we work when installed as a wheel
        # (i.e. `wikijs_mcp/templates/*.md` lives inside the package).
        try:
            from importlib.resources import files

            return Path(str(files("wikijs_mcp") / "templates"))
        except (ImportError, ModuleNotFoundError):
            return Path(__file__).parent / "templates"

    def validate_config(self) -> None:
        """Validate that required configuration is present."""
        if not self.url:
            raise ValueError("WIKIJS_URL environment variable must be set.")
        if not self.api_key:
            raise ValueError("WIKIJS_API_KEY environment variable must be set.")
