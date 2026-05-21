CREATE TABLE IF NOT EXISTS pack_market_prices (
    id SERIAL PRIMARY KEY,
    pack_id VARCHAR(80) NOT NULL,
    market_code VARCHAR(10) NOT NULL,
    price INTEGER NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_pack_market_price UNIQUE (pack_id, market_code)
);

CREATE INDEX IF NOT EXISTS ix_pack_market_prices_pack_id ON pack_market_prices (pack_id);
CREATE INDEX IF NOT EXISTS ix_pack_market_prices_market_code ON pack_market_prices (market_code);
