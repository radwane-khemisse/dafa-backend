ALTER TABLE orders ADD COLUMN IF NOT EXISTS market_code VARCHAR(10) NOT NULL DEFAULT 'ksa';
CREATE INDEX IF NOT EXISTS ix_orders_market_code ON orders (market_code);

ALTER TABLE analytics_events ADD COLUMN IF NOT EXISTS market_code VARCHAR(10);
CREATE INDEX IF NOT EXISTS ix_analytics_events_market_code ON analytics_events (market_code);

CREATE TABLE IF NOT EXISTS market_stores (
  id SERIAL PRIMARY KEY,
  market_code VARCHAR(10) NOT NULL UNIQUE,
  country_code VARCHAR(2) NOT NULL,
  country_name_ar VARCHAR(80) NOT NULL,
  country_name_en VARCHAR(80) NOT NULL,
  active BOOLEAN NOT NULL DEFAULT TRUE,
  currency VARCHAR(3) NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_market_stores_active ON market_stores (active);
CREATE UNIQUE INDEX IF NOT EXISTS ix_market_stores_market_code ON market_stores (market_code);

CREATE TABLE IF NOT EXISTS catalog_market_visibility (
  id SERIAL PRIMARY KEY,
  item_type VARCHAR(20) NOT NULL,
  item_id VARCHAR(80) NOT NULL,
  market_code VARCHAR(10) NOT NULL,
  visible BOOLEAN NOT NULL DEFAULT TRUE,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_catalog_market_visibility_item UNIQUE (item_type, item_id, market_code)
);

CREATE INDEX IF NOT EXISTS ix_catalog_market_visibility_item_id ON catalog_market_visibility (item_id);
CREATE INDEX IF NOT EXISTS ix_catalog_market_visibility_item_type ON catalog_market_visibility (item_type);
CREATE INDEX IF NOT EXISTS ix_catalog_market_visibility_market_code ON catalog_market_visibility (market_code);
CREATE INDEX IF NOT EXISTS ix_catalog_market_visibility_visible ON catalog_market_visibility (visible);

INSERT INTO market_stores (market_code, country_code, country_name_ar, country_name_en, active, currency)
VALUES
  ('ksa', 'SA', 'السعودية', 'Saudi Arabia', TRUE, 'SAR'),
  ('kwt', 'KW', 'الكويت', 'Kuwait', TRUE, 'KWD'),
  ('uae', 'AE', 'الإمارات', 'United Arab Emirates', TRUE, 'AED'),
  ('qat', 'QA', 'قطر', 'Qatar', TRUE, 'QAR'),
  ('bhr', 'BH', 'البحرين', 'Bahrain', TRUE, 'BHD'),
  ('omn', 'OM', 'عمان', 'Oman', TRUE, 'OMR')
ON CONFLICT (market_code) DO NOTHING;
