CREATE TABLE IF NOT EXISTS offer_market_prices (
    id SERIAL PRIMARY KEY,
    product_id VARCHAR(80) NOT NULL,
    offer_id VARCHAR(40) NOT NULL,
    market_code VARCHAR(10) NOT NULL,
    price INTEGER NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_offer_market_price UNIQUE (product_id, offer_id, market_code)
);

CREATE INDEX IF NOT EXISTS ix_offer_market_prices_product_id ON offer_market_prices (product_id);
CREATE INDEX IF NOT EXISTS ix_offer_market_prices_offer_id ON offer_market_prices (offer_id);
CREATE INDEX IF NOT EXISTS ix_offer_market_prices_market_code ON offer_market_prices (market_code);
