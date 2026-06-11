"""PostgreSQL helpers for storing Pokemon data."""

from __future__ import annotations

import json
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterator

import psycopg2
from psycopg2.extras import RealDictCursor

from src.config import Settings, get_settings

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS pokemon (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    height INTEGER,
    weight INTEGER,
    base_experience INTEGER,
    types TEXT NOT NULL,
    abilities TEXT NOT NULL,
    stats JSONB NOT NULL,
    sprite_url TEXT,
    flavor_text TEXT,
    summary TEXT NOT NULL,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pokemon_name ON pokemon (name);
"""


@dataclass
class PokemonRecord:
    id: int
    name: str
    height: int | None
    weight: int | None
    base_experience: int | None
    types: str
    abilities: str
    stats: dict[str, Any]
    sprite_url: str | None
    flavor_text: str | None
    summary: str


@contextmanager
def get_connection(settings: Settings | None = None) -> Iterator[Any]:
    settings = settings or get_settings()
    connection = psycopg2.connect(
        host=settings.postgres_host,
        port=settings.postgres_port,
        dbname=settings.postgres_db,
        user=settings.postgres_user,
        password=settings.postgres_password,
    )
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_schema(settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    with get_connection(settings) as connection:
        with connection.cursor() as cursor:
            cursor.execute(SCHEMA_SQL)


def upsert_pokemon(record: PokemonRecord, settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    with get_connection(settings) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO pokemon (
                    id, name, height, weight, base_experience,
                    types, abilities, stats, sprite_url, flavor_text, summary
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    height = EXCLUDED.height,
                    weight = EXCLUDED.weight,
                    base_experience = EXCLUDED.base_experience,
                    types = EXCLUDED.types,
                    abilities = EXCLUDED.abilities,
                    stats = EXCLUDED.stats,
                    sprite_url = EXCLUDED.sprite_url,
                    flavor_text = EXCLUDED.flavor_text,
                    summary = EXCLUDED.summary,
                    fetched_at = NOW()
                """,
                (
                    record.id,
                    record.name,
                    record.height,
                    record.weight,
                    record.base_experience,
                    record.types,
                    record.abilities,
                    json.dumps(record.stats),
                    record.sprite_url,
                    record.flavor_text,
                    record.summary,
                ),
            )


def fetch_all_pokemon(settings: Settings | None = None) -> list[PokemonRecord]:
    settings = settings or get_settings()
    with get_connection(settings) as connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT id, name, height, weight, base_experience,
                       types, abilities, stats, sprite_url, flavor_text, summary
                FROM pokemon
                ORDER BY id
                """
            )
            rows = cursor.fetchall()

    records: list[PokemonRecord] = []
    for row in rows:
        stats = row["stats"]
        if isinstance(stats, str):
            stats = json.loads(stats)
        records.append(
            PokemonRecord(
                id=row["id"],
                name=row["name"],
                height=row["height"],
                weight=row["weight"],
                base_experience=row["base_experience"],
                types=row["types"],
                abilities=row["abilities"],
                stats=stats,
                sprite_url=row["sprite_url"],
                flavor_text=row["flavor_text"],
                summary=row["summary"],
            )
        )
    return records
