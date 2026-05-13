CREATE TABLE IF NOT EXISTS catalog_visibility (
  id SERIAL PRIMARY KEY,
  item_type VARCHAR(20) NOT NULL,
  item_id VARCHAR(80) NOT NULL,
  hidden BOOLEAN NOT NULL DEFAULT FALSE,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT uq_catalog_visibility_item UNIQUE (item_type, item_id)
);

CREATE INDEX IF NOT EXISTS ix_catalog_visibility_hidden ON catalog_visibility (hidden);
CREATE INDEX IF NOT EXISTS ix_catalog_visibility_item_id ON catalog_visibility (item_id);
CREATE INDEX IF NOT EXISTS ix_catalog_visibility_item_type ON catalog_visibility (item_type);
