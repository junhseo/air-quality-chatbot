import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

import yaml
from dotenv import load_dotenv

load_dotenv()


def _get_config_path() -> Path:
    search_paths = [
        Path(__file__).parent / "config.yaml",
        Path.cwd() / "config.yaml",
        Path.cwd() / "config" / "config.yaml",
    ]
    for path in search_paths:
        if path.exists():
            return path
    raise FileNotFoundError("config.yaml not found.")


def _load_yaml() -> dict:
    with open(_get_config_path(), "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


@dataclass
class PathSettings:
    station_metadata_file: str

    @property
    def station_metadata_path(self) -> Path:
        p = Path(self.station_metadata_file)
        if p.exists():
            return p
        return Path.cwd() / p


@dataclass
class OpenAQSettings:
    base_url: str
    timeout: int
    _api_key: Optional[str] = field(default_factory=lambda: os.getenv("OPENAQ_API_KEY"), repr=False)

    @property
    def api_key(self) -> Optional[str]:
        return self._api_key

    @property
    def headers(self) -> Dict[str, str]:
        return {"X-API-Key": self._api_key or ""}


@dataclass
class APISettings:
    openaq: OpenAQSettings


@dataclass
class QuerySettings:
    default_days: int = 10
    max_days: int = 30


@dataclass
class UISettings:
    language: str = "en"
    title: str = "Air Quality Chatbot"
    page_icon: str = "🌬️"


@dataclass
class Settings:
    paths: PathSettings
    api: APISettings
    query: QuerySettings
    ui: UISettings

    def validate(self) -> bool:
        if not self.api.openaq.api_key:
            raise ValueError("OPENAQ_API_KEY is missing in .env")
        if not self.paths.station_metadata_path.exists():
            raise ValueError(f"Station metadata file not found: {self.paths.station_metadata_path}")
        return True


def _create_settings() -> Settings:
    cfg = _load_yaml()

    return Settings(
        paths=PathSettings(**cfg["paths"]),
        api=APISettings(
            openaq=OpenAQSettings(**cfg["api"]["openaq"])
        ),
        query=QuerySettings(**cfg.get("query", {})),
        ui=UISettings(**cfg.get("ui", {})),
    )


settings = _create_settings()