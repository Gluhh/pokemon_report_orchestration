"""Run the Pokemon Prefect workflow."""

from src.flows.pokemon_flow import pokemon_workflow

if __name__ == "__main__":
    print(pokemon_workflow())
