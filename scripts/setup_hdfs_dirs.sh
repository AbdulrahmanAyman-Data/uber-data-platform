#!/bin/bash
set -e

echo "Creating HDFS directory structure (Rides-only scope, real HVFHS data)..."

# Bronze  raw rides, as landed
hdfs dfs -mkdir -p /data/bronze/rides

# Reference small static files (zone centroids), NOT partitioned, NOT
# produced by Spark. Uploaded once via `hdfs dfs -put` after running
# scripts/compute_zone_centroids.py.
hdfs dfs -mkdir -p /data/reference

# Silver cleaned, deduped rides (trip_id generated, zone-validated)
hdfs dfs -mkdir -p /data/silver/staging_rides_geo

# Gold Star schema (Fact + Dims) + pre-aggregated convenience tables
hdfs dfs -mkdir -p /data/gold/fact_rides
hdfs dfs -mkdir -p /data/gold/dim_date
hdfs dfs -mkdir -p /data/gold/dim_zone
hdfs dfs -mkdir -p /data/gold/agg_trips_daily
hdfs dfs -mkdir -p /data/gold/agg_trips_by_zone
hdfs dfs -mkdir -p /data/gold/agg_trips_by_hour
hdfs dfs -mkdir -p /data/gold/agg_trips_by_company

# Quarantine invalid rides records (bad/unknown zone / bad timestamps /
# bad duration / reported-vs-computed duration mismatch)
hdfs dfs -mkdir -p /data/quarantine/rides

# Hive warehouse
hdfs dfs -mkdir -p /user/hive/warehouse

echo "Setting ownership..."

# Hadoop owns the data directories by default
hdfs dfs -chown -R hdfs:hadoop /data

# NiFi needs WRITE access to the Bronze rides landing zone
hdfs dfs -chown nifi:hadoop /data/bronze/rides

# Hive warehouse
hdfs dfs -chown -R hdfs:hadoop /user/hive/warehouse

echo "Done. Current structure:"
hdfs dfs -ls -R /data
