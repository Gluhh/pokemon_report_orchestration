"""Prefect workflow to fetch Pokemon data, store in PostgreSQL, and build a Word report."""

from __future__ import annotations

from pathlib import Path

from prefect import flow, task, unmapped
from prefect.futures import wait

from src.config import Settings, get_settings
from src.database import PokemonRecord, fetch_all_pokemon, initialize_schema, upsert_pokemon
from src.pokeapi_client import PokeAPIClient, PokemonListItem, pokemon_data_to_record
from src.report_generator import generate_pokemon_report


@task(name="Initialize Database Schema", retries=2, retry_delay_seconds=5)
def init_database_task(settings: Settings | None = None) -> None:
    initialize_schema(settings)


@task(name="Fetch Pokemon List", retries=3, retry_delay_seconds=10)
def fetch_pokemon_list_task(settings: Settings | None = None) -> list[PokemonListItem]:
    settings = settings or get_settings()
    client = PokeAPIClient()
    return client.fetch_pokemon_list(settings.pokeapi_list_url)


@task(name="Fetch Pokemon Detail", retries=3, retry_delay_seconds=10)
def fetch_pokemon_detail_task(pokemon_url: str) -> PokemonRecord:
    client = PokeAPIClient()
    pokemon_data = client.fetch_pokemon_detail(pokemon_url)
    flavor_text = client.fetch_species_flavor_text(pokemon_data["species"]["url"])
    return pokemon_data_to_record(pokemon_data, flavor_text)


@task(name="Save Pokemon Record", retries=2, retry_delay_seconds=5)
def save_pokemon_record_task(record: PokemonRecord, settings: Settings | None = None) -> int:
    upsert_pokemon(record, settings)
    return record.id


@task(name="Generate Word Report", retries=1, retry_delay_seconds=5)
def generate_report_task(settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    records = fetch_all_pokemon(settings)
    report_path = generate_pokemon_report(records, settings)
    return str(report_path)


@flow(name="Pokemon ETL and Report Flow", log_prints=True)
def pokemon_workflow() -> dict[str, str | int]:
    settings = get_settings()
    print("Starting Pokemon workflow...")

    init_database_task(settings)
    pokemon_list = fetch_pokemon_list_task(settings)
    print(f"Fetched {len(pokemon_list)} Pokemon from PokeAPI.")

    detail_futures = fetch_pokemon_detail_task.map(
        [item.url for item in pokemon_list]
    )
    wait(detail_futures)
    records = [future.result() for future in detail_futures]

    save_futures = save_pokemon_record_task.map(records, settings=unmapped(settings))
    wait(save_futures)
    saved_ids = [future.result() for future in save_futures]

    report_path = generate_report_task(settings)
    print(f"Report generated at: {report_path}")

    return {
        "pokemon_count": len(saved_ids),
        "report_path": report_path,
    }


if __name__ == "__main__":
    result = pokemon_workflow()
    print(result)
