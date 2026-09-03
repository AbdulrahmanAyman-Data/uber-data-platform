import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.spark_session import get_spark_session
from common.cleaning import (
    deduplicate_rides,
    generate_trip_id,
    standardize_rides,
    drop_operational_columns,
    handle_nulls_rides,
    split_invalid_rides,
    add_derived_columns_rides,
)

BRONZE_PATH = "hdfs://uber-hadoop-master:9000/data/bronze/rides"
SILVER_PATH = "hdfs://uber-hadoop-master:9000/data/silver/staging_rides_geo"
QUARANTINE_PATH = "hdfs://uber-hadoop-master:9000/data/quarantine/rides"


def run():
    spark = get_spark_session("bronze_to_silver_rides")

    print(f"[Rides Bronze -> Silver] Reading from: {BRONZE_PATH}")
    bronze_df = (
    spark.read
    .option("mergeSchema", "true")
    .parquet(BRONZE_PATH)
    .limit(1000)
    )

    print(f"[Rides Bronze -> Silver] Total records read: {bronze_df.count()}")

    df = generate_trip_id(bronze_df)
    df = drop_operational_columns(df)
    df = handle_nulls_rides(df)

    valid_df, quarantine_df = split_invalid_rides(df)

    valid_df = standardize_rides(valid_df)
    valid_df = add_derived_columns_rides(valid_df)
    valid_df = deduplicate_rides(valid_df)


    valid_count = valid_df.count()
    quarantine_count = quarantine_df.count()

    print(f"[Rides Bronze -> Silver] Valid: {valid_count} | Quarantine: {quarantine_count}")

    (
        valid_df.write
        .mode("overwrite")
        .partitionBy("year", "month", "day")
        .parquet(SILVER_PATH)
    )

    if quarantine_count > 0:
        quarantine_df.write.mode("overwrite").parquet(QUARANTINE_PATH)

    print("[Rides Bronze -> Silver] Completed successfully.")
    spark.stop()


if __name__ == "__main__":
    run()
