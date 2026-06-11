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
