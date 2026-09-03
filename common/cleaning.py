
from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from common.schemas import (
    RIDES_SILVER_SCHEMA, RIDES_COLUMN_RENAME_MAP
)


def standardize_columns(df: DataFrame, schema, rename_map: dict) -> DataFrame:

    for source_col, target_col in rename_map.items():
        if source_col in df.columns and source_col != target_col:
            df = df.withColumnRenamed(source_col, target_col)

    for field in schema.fields:
        if field.name  in df.columns:
             df = df.withColumn(field.name, F.col(field.name).cast(field.dataType))

    return df.select([f.name for f in schema.fields])

# =========================================================
# drop columns
# =========================================================
def drop_operational_columns(df):
    columns_to_drop = [
        "dispatching_base_num",
        "originating_base_num",
        "shared_request_flag",
        "shared_match_flag",
        "access_a_ride_flag",
        "wav_request_flag",
        "wav_match_flag"
    ]

    return df.drop(*columns_to_drop)

# =========================================================
# DROP DUPLICATES
# =========================================================
def deduplicate_rides(df):
    return df.dropDuplicates([
        "hvfhs_license_num",
        "request_datetime",
        "start_time",
        "end_time",
        "pu_location_id",
        "do_location_id"
    ])


# =========================================================
# RIDES  (real source: NYC TLC HVFHS trip records)
# =========================================================
def generate_trip_id(df):
    return df.withColumn(
        "trip_id",
        F.monotonically_increasing_id()
    )


def standardize_rides(df):
    return standardize_columns(
        df,
        RIDES_SILVER_SCHEMA,
        RIDES_COLUMN_RENAME_MAP
    )


def handle_nulls_rides(df):
    return df.withColumn(
        "on_scene_datetime",
        F.coalesce(
            F.col("on_scene_datetime"),
            F.col("request_datetime")
        )
    )

def split_invalid_rides(df):
    valid_conditions = (
        F.col("hvfhs_license_num").isNotNull()
        & F.col("request_datetime").isNotNull()
        & F.col("pickup_datetime").isNotNull()
        & F.col("dropoff_datetime").isNotNull()

        & (F.col("request_datetime") <= F.col("pickup_datetime"))
        & (F.col("pickup_datetime") < F.col("dropoff_datetime"))

        & F.col("PULocationID").between(1, 265)
        & F.col("DOLocationID").between(1, 265)

        & (F.col("trip_time") > 0)
        & (F.col("trip_miles") >= 0.0)

        & (F.col("base_passenger_fare") >= 0.0)
        & (F.col("tolls") >= 0.0)
        & (F.col("bcf") >= 0.0)
        & (F.col("sales_tax") >= 0.0)
        & (F.col("congestion_surcharge") >= 0.0)
        & (F.col("airport_fee") >= 0.0)
        & (F.col("tips") >= 0.0)
        & (F.col("driver_pay") >= 0.0)
    )

    df_clean = df.filter(valid_conditions)

    df_bad_records = (
        df.filter(~valid_conditions)
        .withColumn(
            "quarantine_reason",
            F.lit("failed_data_quality_validation")
        )
    )

    return df_clean, df_bad_records


def add_derived_columns_rides(df):
    return (
        df.withColumn(
            "trip_duration_sec",
            F.unix_timestamp("end_time")
            - F.unix_timestamp("start_time")
        )
        .withColumn("year", F.year("start_time"))
        .withColumn("month", F.month("start_time"))
        .withColumn("day", F.dayofmonth("start_time"))
    )



