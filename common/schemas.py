
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, DoubleType,
    LongType, TimestampType, DateType, BooleanType
)

RIDES_SILVER_SCHEMA = StructType([

    # Trip identification
    StructField("trip_id", LongType(), True),

    # Provider
    StructField("hvfhs_license_num", StringType(), True),

    # Request / trip timestamps
    StructField("request_datetime", TimestampType(), True),
    StructField("on_scene_datetime", TimestampType(), True),
    StructField("start_time", TimestampType(), True),
    StructField("end_time", TimestampType(), True),

    # Locations
    StructField("pu_location_id", IntegerType(), True),
    StructField("do_location_id", IntegerType(), True),

    # Trip metrics
    StructField("distance", DoubleType(), True),
    StructField("reported_duration_sec", LongType(), True),

    # Financial fields
    StructField("base_passenger_fare", DoubleType(), True),
    StructField("tolls", DoubleType(), True),
    StructField("bcf", DoubleType(), True),
    StructField("sales_tax", DoubleType(), True),
    StructField("congestion_surcharge", DoubleType(), True),
    StructField("airport_fee", DoubleType(), True),
    StructField("tips", DoubleType(), True),
    StructField("driver_pay", DoubleType(), True),
])


RIDES_COLUMN_RENAME_MAP = {

    # Provider
    "hvfhs_license_num": "hvfhs_license_num",

    # Locations
    "PULocationID": "pu_location_id",
    "DOLocationID": "do_location_id",

    # Timestamps
    "request_datetime": "request_datetime",
    "on_scene_datetime": "on_scene_datetime",
    "pickup_datetime": "start_time",
    "dropoff_datetime": "end_time",

    # Trip metrics
    "trip_miles": "distance",
    "trip_time": "reported_duration_sec",

    # Financial fields
    "base_passenger_fare": "base_passenger_fare",
    "tolls": "tolls",
    "bcf": "bcf",
    "sales_tax": "sales_tax",
    "congestion_surcharge": "congestion_surcharge",
    "airport_fee": "airport_fee",
    "tips": "tips",
    "driver_pay": "driver_pay",
}

# =========================================================
# STAR SCHEMA — Rides-only Gold layer (Fact_Rides + Dim_Date + Dim_Zone)
# =========================================================
DIM_DATE_SCHEMA = StructType([
    StructField("date_key",     IntegerType(), True),   # PK, e.g. 20240115
    StructField("date",    DateType(), True),
    StructField("year",         IntegerType(), True),
    StructField("month",        IntegerType(), True),
    StructField("day",          IntegerType(), True),
    StructField("day_of_week",  StringType(), True),
    StructField("is_weekend",   BooleanType(), True),
])

DIM_ZONE_SCHEMA = StructType([
    StructField("location_id",    IntegerType(), True),  # PK — TLC taxi zone LocationID (natural key)
    StructField("borough",        StringType(), True),
    StructField("zone_name",      StringType(), True),
    StructField("service_zone",   StringType(), True),
    StructField("centroid_lat",   DoubleType(), True),
    StructField("centroid_lon",   DoubleType(), True),
    StructField("polygon_wkt", StringType(), True)
])

FACT_RIDES_SCHEMA = StructType([
    StructField("trip_id",             StringType(), True),
    StructField("date_key",            IntegerType(), True),   # FK -> Dim_Date
    StructField("pu_location_id",      IntegerType(), True),   # FK -> Dim_Zone
    StructField("do_location_id",      IntegerType(), True),   # FK -> Dim_Zone
    StructField("hvfhs_license_num",   StringType(), True),    # degenerate dimension
    StructField("start_time",          TimestampType(), True),
    StructField("end_time",            TimestampType(), True),
    StructField("trip_duration_sec",   LongType(), True),      # computed: end_time - start_time
    StructField("reported_duration_sec", LongType(), True),    # source trip_time, kept for transparency
    StructField("distance",            DoubleType(), True),    # miles
    StructField("pickup_hour",         IntegerType(), True),   # degenerate dimension
    StructField("year",                IntegerType(), True),
    StructField("month",               IntegerType(), True),
    StructField("day",                 IntegerType(), True),
])



