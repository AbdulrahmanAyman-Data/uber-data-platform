import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.spark_session import get_spark_session
from common.star_schema import build_fact_rides, build_dim_date, build_dim_zone


SILVER_PATH = "hdfs://uber-hadoop-master:9000/data/silver/rides"
GOLD_PATH = "hdfs://uber-hadoop-master:9000/data/gold"

ZONE_GEOMETRIES_PATH = "hdfs://uber-hadoop-master:9000/data/reference/taxi_zone_geometries.csv"


def write_gold_table(df, name: str, partition_cols: list = None):
    print(f"[Silver -> Gold] Writing {name} ...")
    writer = df.write.mode("overwrite")
    if partition_cols:
        writer = writer.partitionBy(*partition_cols)
    writer.parquet(f"{GOLD_PATH}/{name}")
    print(f"[Silver -> Gold] {name} completed successfully.")


def run():
    spark = get_spark_session("silver_to_gold_rides_star_schema")

    print(f"[Silver -> Gold] Reading Silver rides from: {SILVER_PATH}")
    rides_silver_df = spark.read.parquet(SILVER_PATH)
    print(f"[Silver -> Gold] Rides in Silver: {rides_silver_df.count()}")

    # --- Dimensions ---
    dim_date_df = build_dim_date(rides_silver_df)
    dim_zone_df = build_dim_zone(spark, ZONE_GEOMETRIES_PATH)

    write_gold_table(dim_date_df, "dim_date")
    write_gold_table(dim_zone_df, "dim_zone")

    # --- Fact 
    fact_rides_df = build_fact_rides(rides_silver_df)

    write_gold_table(fact_rides_df, "fact_rides", ["year", "month", "day"])
  

    print("[Silver -> Gold] Star schema (Fact_Rides + Dim_Date + Dim_Zone) completed successfully.")
    spark.stop()


if __name__ == "__main__":
    run()
