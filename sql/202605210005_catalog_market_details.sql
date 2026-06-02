CREATE TABLE IF NOT EXISTS product_market_details (
    id SERIAL PRIMARY KEY,
    product_id VARCHAR(80) NOT NULL,
    market_code VARCHAR(10) NOT NULL,
    sku VARCHAR(120) NOT NULL,
    cost FLOAT NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_product_market_detail UNIQUE (product_id, market_code)
);

CREATE INDEX IF NOT EXISTS ix_product_market_details_product_id ON product_market_details (product_id);
CREATE INDEX IF NOT EXISTS ix_product_market_details_market_code ON product_market_details (market_code);

CREATE TABLE IF NOT EXISTS pack_market_details (
    id SERIAL PRIMARY KEY,
    pack_id VARCHAR(80) NOT NULL,
    market_code VARCHAR(10) NOT NULL,
    sku VARCHAR(120) NOT NULL,
    cost FLOAT NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_pack_market_detail UNIQUE (pack_id, market_code)
);

CREATE INDEX IF NOT EXISTS ix_pack_market_details_pack_id ON pack_market_details (pack_id);
CREATE INDEX IF NOT EXISTS ix_pack_market_details_market_code ON pack_market_details (market_code);
