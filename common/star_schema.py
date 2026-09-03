from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F


def build_fact_rides(rides_silver_df: DataFrame) -> DataFrame:
    fact = (
        rides_silver_df
        .withColumn("date_key", F.date_format("start_time", "yyyyMMdd").cast("int"))
        .withColumn("pickup_hour", F.hour("start_time"))
    )
    return fact.select(
        "trip_id", "date_key", "pu_location_id", "do_location_id",
        "hvfhs_license_num", "start_time", "end_time",
        "trip_duration_sec", "reported_duration_sec", "distance",
        "pickup_hour", "year", "month", "day",
    )


def build_dim_date(rides_silver_df: DataFrame) -> DataFrame:
    return (
        rides_silver_df
        .select(F.to_date("start_time").alias("full_date"))
        .distinct()
        .withColumn("date_key", F.date_format("full_date", "yyyyMMdd").cast("int"))
        .withColumn("year", F.year("full_date"))
        .withColumn("month", F.month("full_date"))
        .withColumn("day", F.dayofmonth("full_date"))
        .withColumn("day_of_week", F.date_format("full_date", "EEEE"))
        .withColumn("is_weekend", F.dayofweek("full_date").isin(1, 7))  # Sun=1, Sat=7
        .select("date_key", "full_date", "year", "month", "day", "day_of_week", "is_weekend")
    )


def build_dim_zone(spark: SparkSession, zone_centroids_path: str) -> DataFrame:

    raw = (
        spark.read
        .option("header", "true")
        .option("inferSchema", "true")
        .csv(zone_centroids_path)
    )

    return (
        raw.select(
            "location_id",
            "borough",
            "zone_name",
            "service_zone",
            "polygon_wkt",
            "centroid_lat",
            "centroid_lon",
            "geo_hash",
            "h3_resolution",
        )
    )