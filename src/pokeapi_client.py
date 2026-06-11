"""PokeAPI client and Pokemon data transformation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

from src.database import PokemonRecord

DEFAULT_TIMEOUT = 30


@dataclass
class PokemonListItem:
    name: str
    url: str


class PokeAPIClient:
    def __init__(self, timeout: int = DEFAULT_TIMEOUT) -> None:
        self.timeout = timeout
        self.session = requests.Session()

    def fetch_pokemon_list(self, list_url: str) -> list[PokemonListItem]:
        results: list[PokemonListItem] = []
        url: str | None = list_url

        while url:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            payload = response.json()
            results.extend(
                PokemonListItem(name=item["name"], url=item["url"])
                for item in payload["results"]
            )
            url = payload.get("next")

        return results

    def fetch_pokemon_detail(self, url: str) -> dict[str, Any]:
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def fetch_species_flavor_text(self, species_url: str) -> str | None:
        response = self.session.get(species_url, timeout=self.timeout)
        response.raise_for_status()
        species = response.json()

        english_entries = [
            entry["flavor_text"].replace("\n", " ").replace("\f", " ").strip()
            for entry in species.get("flavor_text_entries", [])
            if entry.get("language", {}).get("name") == "en"
        ]
        if not english_entries:
            return None
        return english_entries[-1]

    def download_sprite(self, sprite_url: str, destination: str) -> str:
        response = self.session.get(sprite_url, timeout=self.timeout)
        response.raise_for_status()
        with open(destination, "wb") as sprite_file:
            sprite_file.write(response.content)
        return destination


def extract_sprite_url(pokemon_data: dict[str, Any]) -> str | None:
    other_sprites = pokemon_data.get("sprites", {}).get("other", {})
    official = other_sprites.get("official-artwork", {})
    if official.get("front_default"):
        return official["front_default"]
    return pokemon_data.get("sprites", {}).get("front_default")


def build_summary(pokemon_data: dict[str, Any], flavor_text: str | None) -> str:
    types = ", ".join(
        slot["type"]["name"].title()
        for slot in sorted(pokemon_data.get("types", []), key=lambda item: item["slot"])
    )
    abilities = ", ".join(
        ability["ability"]["name"].replace("-", " ").title()
        for ability in pokemon_data.get("abilities", [])
    )
    stats = {
        stat["stat"]["name"]: stat["base_stat"]
        for stat in pokemon_data.get("stats", [])
    }
    stat_lines = ", ".join(f"{name}: {value}" for name, value in stats.items())

    height_dm = pokemon_data.get("height", 0)
    weight_hg = pokemon_data.get("weight", 0)
    height_m = height_dm / 10 if height_dm else 0
    weight_kg = weight_hg / 10 if weight_hg else 0

    parts = [
        f"Types: {types or 'Unknown'}.",
        f"Abilities: {abilities or 'Unknown'}.",
        f"Height: {height_m:.1f} m. Weight: {weight_kg:.1f} kg.",
        f"Base experience: {pokemon_data.get('base_experience', 'N/A')}.",
        f"Base stats: {stat_lines}.",
    ]
    if flavor_text:
        parts.append(f"Pokedex entry: {flavor_text}")
    return " ".join(parts)


def pokemon_data_to_record(
    pokemon_data: dict[str, Any],
    flavor_text: str | None,
) -> PokemonRecord:
    types = ", ".join(
        slot["type"]["name"].title()
        for slot in sorted(pokemon_data.get("types", []), key=lambda item: item["slot"])
    )
    abilities = ", ".join(
        ability["ability"]["name"].replace("-", " ").title()
        for ability in pokemon_data.get("abilities", [])
    )
    stats = {
        stat["stat"]["name"]: stat["base_stat"]
        for stat in pokemon_data.get("stats", [])
    }

    return PokemonRecord(
        id=pokemon_data["id"],
        name=pokemon_data["name"].replace("-", " ").title(),
        height=pokemon_data.get("height"),
        weight=pokemon_data.get("weight"),
        base_experience=pokemon_data.get("base_experience"),
        types=types,
        abilities=abilities,
        stats=stats,
        sprite_url=extract_sprite_url(pokemon_data),
        flavor_text=flavor_text,
        summary=build_summary(pokemon_data, flavor_text),
    )
