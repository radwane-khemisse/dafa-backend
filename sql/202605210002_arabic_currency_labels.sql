ALTER TABLE orders ALTER COLUMN currency TYPE VARCHAR(20);
ALTER TABLE orders ALTER COLUMN currency SET DEFAULT 'ريال';
ALTER TABLE market_stores ALTER COLUMN currency TYPE VARCHAR(20);

UPDATE market_stores SET currency = 'ريال' WHERE market_code IN ('ksa', 'qat', 'omn');
UPDATE market_stores SET currency = 'دينار' WHERE market_code IN ('kwt', 'bhr');
UPDATE market_stores SET currency = 'درهم' WHERE market_code = 'uae';
