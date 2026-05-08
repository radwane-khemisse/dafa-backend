ALTER TABLE orders
  ADD COLUMN IF NOT EXISTS ip_country_code VARCHAR(2),
  ADD COLUMN IF NOT EXISTS ip_city VARCHAR(120),
  ADD COLUMN IF NOT EXISTS ip_is_vpn BOOLEAN,
  ADD COLUMN IF NOT EXISTS ip_is_valid_ksa BOOLEAN NOT NULL DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS ip_validation_reason VARCHAR(255);

CREATE TABLE IF NOT EXISTS analytics_events (
  id SERIAL PRIMARY KEY,
  event_name VARCHAR(80) NOT NULL,
  event_id VARCHAR(255),
  session_id VARCHAR(255),
  product_id VARCHAR(80),
  path TEXT,
  referrer TEXT,
  user_agent TEXT,
  ip_address VARCHAR(64),
  ip_country_code VARCHAR(2),
  ip_city VARCHAR(120),
  ip_is_vpn BOOLEAN,
  ip_is_valid_ksa BOOLEAN NOT NULL DEFAULT FALSE,
  ip_validation_reason VARCHAR(255),
  utm_source VARCHAR(255),
  utm_medium VARCHAR(255),
  utm_campaign VARCHAR(255),
  utm_content VARCHAR(255),
  utm_term VARCHAR(255),
  metadata_json TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_analytics_events_created_at ON analytics_events (created_at);
CREATE INDEX IF NOT EXISTS ix_analytics_events_event_id ON analytics_events (event_id);
CREATE INDEX IF NOT EXISTS ix_analytics_events_event_name ON analytics_events (event_name);
CREATE INDEX IF NOT EXISTS ix_analytics_events_ip_country_code ON analytics_events (ip_country_code);
CREATE INDEX IF NOT EXISTS ix_analytics_events_ip_is_valid_ksa ON analytics_events (ip_is_valid_ksa);
CREATE INDEX IF NOT EXISTS ix_analytics_events_product_id ON analytics_events (product_id);
CREATE INDEX IF NOT EXISTS ix_analytics_events_session_id ON analytics_events (session_id);
