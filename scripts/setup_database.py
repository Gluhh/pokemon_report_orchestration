"""Wait for PostgreSQL, create database/user, and initialize schema."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import Settings, get_settings  # noqa: E402
from src.database import initialize_schema  # noqa: E402

try:
    import psycopg2
    from psycopg2 import sql
except ImportError as exc:
    raise SystemExit("Install dependencies first: pip install -r requirements.txt") from exc


def wait_for_admin_postgres(settings: Settings, max_attempts: int = 10, delay_seconds: int = 2) -> None:
    admin_user = os.getenv("POSTGRES_ADMIN_USER", "pokemon")
    admin_password = os.getenv("POSTGRES_ADMIN_PASSWORD", "pokemon123")

    if not admin_password:
        raise SystemExit(
            "Set POSTGRES_ADMIN_PASSWORD in .env to the local postgres superuser password.\n"
            "If you used Docker Compose, the app user/database are created automatically."
        )

    for attempt in range(1, max_attempts + 1):
        try:
            connection = psycopg2.connect(
                host=settings.postgres_host,
                port=settings.postgres_port,
                dbname="pokemon_db",
                user=admin_user,
                password=admin_password,
            )
            connection.close()
            print("PostgreSQL admin connection is ready.")
            return
        except psycopg2.OperationalError as error:
            print(f"Attempt {attempt}/{max_attempts}: PostgreSQL not ready yet ({error}).")
            time.sleep(delay_seconds)

    raise SystemExit(
        "Could not connect to PostgreSQL. Start it with:\n"
        "  docker compose up -d\n"
        "Or install PostgreSQL locally and update .env."
    )


def wait_for_app_postgres(settings: Settings, max_attempts: int = 30, delay_seconds: int = 2) -> None:
    for attempt in range(1, max_attempts + 1):
        try:
            connection = psycopg2.connect(
                host=settings.postgres_host,
                port=settings.postgres_port,
                dbname=settings.postgres_db,
                user=settings.postgres_user,
                password=settings.postgres_password,
            )
            connection.close()
            print("Application database connection is ready.")
            return
        except psycopg2.OperationalError as error:
            print(f"Attempt {attempt}/{max_attempts}: app DB not ready yet ({error}).")
            time.sleep(delay_seconds)

    raise SystemExit("Could not connect to the application database.")


def create_database_and_user(settings: Settings) -> None:
    admin_user = os.getenv("POSTGRES_ADMIN_USER", "postgres")
    admin_password = os.getenv("POSTGRES_ADMIN_PASSWORD", "")

    connection = psycopg2.connect(
        host=settings.postgres_host,
        port=settings.postgres_port,
        dbname="postgres",
        user=admin_user,
        password=admin_password,
    )
    connection.autocommit = True

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM pg_roles WHERE rolname = %s",
                (settings.postgres_user,),
            )
            if cursor.fetchone() is None:
                cursor.execute(
                    sql.SQL("CREATE USER {} WITH PASSWORD %s").format(
                        sql.Identifier(settings.postgres_user)
                    ),
                    (settings.postgres_password,),
                )
                print(f"Created user '{settings.postgres_user}'.")

            cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (settings.postgres_db,),
            )
            if cursor.fetchone() is None:
                cursor.execute(
                    sql.SQL("CREATE DATABASE {} OWNER {}").format(
                        sql.Identifier(settings.postgres_db),
                        sql.Identifier(settings.postgres_user),
                    )
                )
                print(f"Created database '{settings.postgres_db}'.")
    finally:
        connection.close()


def main() -> None:
    settings = get_settings()

    if os.getenv("POSTGRES_ADMIN_PASSWORD"):
        wait_for_admin_postgres(settings)
        create_database_and_user(settings)

    wait_for_app_postgres(settings)
    initialize_schema(settings)
    print("Database schema initialized.")


if __name__ == "__main__":
    main()
