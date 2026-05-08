#!/usr/bin/env sh
set -eu

: "${MAXMIND_ACCOUNT_ID:?Set MAXMIND_ACCOUNT_ID}"
: "${MAXMIND_LICENSE_KEY:?Set MAXMIND_LICENSE_KEY}"

OUTPUT_DIR="${MAXMIND_OUTPUT_DIR:-./maxmind}"
EDITION_IDS="${MAXMIND_EDITION_IDS:-GeoLite2-City GeoLite2-Country GeoLite2-Anonymous-IP}"

mkdir -p "$OUTPUT_DIR"

for edition in $EDITION_IDS; do
  archive="$OUTPUT_DIR/$edition.tar.gz"
  url="https://download.maxmind.com/geoip/databases/$edition/download?suffix=tar.gz"
  curl -fsSL -u "$MAXMIND_ACCOUNT_ID:$MAXMIND_LICENSE_KEY" "$url" -o "$archive"
  tar -xzf "$archive" -C "$OUTPUT_DIR"
  found="$(find "$OUTPUT_DIR" -name "$edition.mmdb" -type f | sort | tail -n 1)"
  cp "$found" "$OUTPUT_DIR/$edition.mmdb"
done

echo "MaxMind databases are ready in $OUTPUT_DIR"
