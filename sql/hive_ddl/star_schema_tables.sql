
CREATE SCHEMA IF NOT EXISTS hive.default;

-- =========================================================
-- dim_date  
-- =========================================================
CREATE TABLE IF NOT EXISTS hive.default.dim_date (
    date_key      INTEGER,     -- PK, YYYYMMDD
    full_date     DATE,
    year          INTEGER,
    month         INTEGER,
    day           INTEGER,
    day_of_week   VARCHAR,
    is_weekend    BOOLEAN
)
WITH (
    format = 'PARQUET',
    external_location = 'hdfs://uber-hadoop-master:9000/data/gold/dim_date'
);

-- =========================================================
-- dim_zone  
-- =========================================================
CREATE TABLE IF NOT EXISTS hive.default.dim_zone (
    location_id     INTEGER,   -- PK, TLC taxi zone LocationID
    borough         VARCHAR,
    zone_name       VARCHAR,
    service_zone    VARCHAR,
    polygon_wkt     VARCHAR,   -- full zone polygon, WKT, WGS84 (lat/lon degrees)
    centroid_lat    DOUBLE,
    centroid_lon    DOUBLE,
    geo_hash        VARCHAR,   -- H3 cell of the centroid (computed upstream, not by Trino/Spark)
    h3_resolution   INTEGER
)
WITH (
    format = 'PARQUET',
    external_location = 'hdfs://uber-hadoop-master:9000/data/gold/dim_zone'
);

-- =========================================================
-- fact_rides  
-- =========================================================
CREATE TABLE IF NOT EXISTS hive.default.fact_rides (
    trip_id                 BIGINT,
    date_key                INTEGER,
    pu_location_id          INTEGER,
    do_location_id          INTEGER,
    hvfhs_license_num       VARCHAR,
    start_time              TIMESTAMP,
    end_time                TIMESTAMP,
    trip_duration_sec       BIGINT,
    reported_duration_sec   BIGINT,
    distance                DOUBLE,   -- miles
    pickup_hour             INTEGER,
    year                    INTEGER,
    month                   INTEGER,
    day                     INTEGER
)
WITH (
    format = 'PARQUET',
    external_location = 'hdfs://uber-hadoop-master:9000/data/gold/fact_rides',
    partitioned_by = ARRAY['year', 'month', 'day']
);


