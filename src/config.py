"""Project configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    postgres_host: str
    postgres_port: int
    postgres_db: str
    postgres_user: str
    postgres_password: str
    pokeapi_list_url: str
    report_output_dir: Path
    sprites_cache_dir: Path

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


def get_settings() -> Settings:
    return Settings(
        postgres_host=os.getenv("POSTGRES_HOST", "localhost"),
        postgres_port=int(os.getenv("POSTGRES_PORT", "5432")),
        postgres_db=os.getenv("POSTGRES_DB", "pokemon_db"),
        postgres_user=os.getenv("POSTGRES_USER", "pokemon"),
        postgres_password=os.getenv("POSTGRES_PASSWORD", "pokemon123"),
        pokeapi_list_url=os.getenv(
            "POKEAPI_LIST_URL",
            "https://pokeapi.co/api/v2/pokemon?limit=1350",
        ),
        report_output_dir=PROJECT_ROOT
        / os.getenv("REPORT_OUTPUT_DIR", "output"),
        sprites_cache_dir=PROJECT_ROOT
        / os.getenv("SPRITES_CACHE_DIR", "output/sprites"),
    )
