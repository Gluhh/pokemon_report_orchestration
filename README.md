# Prefect Pokemon ETL

Prefect workflow that fetches all 1350 Pokemon from [PokeAPI](https://pokeapi.co/api/v2/pokemon?limit=1350), stores the data in a local PostgreSQL database, and generates a Word report with sprites and summaries in National Dex order.

## Project structure

```
Pokemon_repost_prefect/
├── docker-compose.yml          # Local PostgreSQL
├── database/init.sql           # Database schema
├── requirements.txt
├── run_flow.py                 # Execute the workflow
├── scripts/
│   ├── setup_database.py       # Wait for Postgres and init schema
│   └── start_prefect_server.py # Start Prefect UI/API server
└── src/
    ├── config.py
    ├── database.py
    ├── pokeapi_client.py
    ├── report_generator.py
    └── flows/pokemon_flow.py
```

## Prerequisites

- Python 3.11+
- Docker Desktop (recommended for PostgreSQL) or a local PostgreSQL installation

## Setup

1. Create a virtual environment and install dependencies:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Copy environment variables:

```powershell
Copy-Item .env.example .env
```

3. Start PostgreSQL with Docker:

```powershell
docker compose up -d
python scripts/setup_database.py
```

If you installed PostgreSQL locally instead of Docker, set the superuser password in `.env`:

```env
POSTGRES_ADMIN_PASSWORD=your_postgres_password
```

Then run:

```powershell
python scripts/setup_database.py
```

## Run the Prefect server

Start the local Prefect server (UI at http://127.0.0.1:4200):

```powershell
python scripts/start_prefect_server.py
```

In another terminal, run the workflow:

```powershell
python run_flow.py
```

Or serve the flow for repeated runs from the Prefect UI:

```powershell
prefect deploy src/flows/pokemon_flow.py:pokemon_workflow --name pokemon-etl
```

## Workflow steps

1. Initialize PostgreSQL schema
2. Fetch the list of all Pokemon from PokeAPI
3. Fetch each Pokemon detail and species flavor text (mapped tasks with retries)
4. Upsert records into PostgreSQL
5. Generate a Word report in `output/` with sprites and summaries ordered by Dex number

## Outputs

- PostgreSQL table: `pokemon`
- Word report: `output/pokemon_report_YYYYMMDD_HHMMSS.docx`
- Cached sprites: `output/sprites/`

## PostgreSQL without Docker

Install PostgreSQL locally, create a database/user matching `.env`, then run:

```powershell
python scripts/setup_database.py
python run_flow.py
```
