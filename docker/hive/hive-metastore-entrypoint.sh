#!/bin/bash
# docker/hive/hive-metastore-entrypoint.sh
#
# Makes the Hive Metastore container fully self-sufficient: it checks whether
# the schema already exists in Postgres, initializes it ONLY if missing, then
# hands off to the image's original entrypoint. No teammate ever needs to run
# schematool manually or flip IS_RESUME true/false again.

set -e

echo "[hive-metastore-init] Checking whether the Metastore schema is already initialized..."

if /opt/hive/bin/schematool -dbType postgres -info > /tmp/schema_info.log 2>&1; then
    echo "[hive-metastore-init] Schema already initialized — skipping initSchema."
else
    echo "[hive-metastore-init] Schema not found — running initSchema now (first run)..."
    /opt/hive/bin/schematool -dbType postgres -initSchema
    echo "[hive-metastore-init] Schema initialized successfully."
fi

# From here on, always tell the original entrypoint to skip its own schema-init
# logic — we already guaranteed the schema is in a good state above. This is
# what makes it safe to leave IS_RESUME fixed in docker-compose.yml forever.
export IS_RESUME=true

echo "[hive-metastore-init] Handing off to the original Hive entrypoint..."
exec /entrypoint.sh
