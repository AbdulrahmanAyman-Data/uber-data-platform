import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, 
    coalesce, 
    monotonically_increasing_id, 
    udf, 
    broadcast
)
from pyspark.sql.types import StringType

# 1. Enforce HDFS Permissions via Environment Variable
os.environ["HADOOP_USER_NAME"] = "hdfs"

# 2. Initialize Spark Session with Memory Tuning
spark = SparkSession.builder \
    .appName("Uber_Medallion_Silver_Layer_Production") \
    .config("spark.driver.memory", "4g") \
    .config("spark.executor.memory", "4g") \
    .config("spark.sql.shuffle.partitions", "200") \
    .getOrCreate()

print("Spark Session initialized successfully.")

# 3. Define H3 Geospatial UDF (Resolution 9)
@udf(returnType=StringType())
def compute_h3(lat, lon, resolution=9):
    if lat is None or lon is None:
        return None
    try:
        import h3
        return h3.latlng_to_cell(float(lat), float(lon), resolution)
    except Exception:
        return None

# 4. Load Bronze Data
# Note: Remove .limit() or .sample() when running your full production dataset
print("Loading Bronze data from HDFS...")
df_bronze = spark.read.parquet("hdfs://uber-hadoop-master:9000/data/bronze/rides/*.parquet")
df_base_data = df_bronze.limit(500000) # Remove limit for full 80M execution

# 5. Drop Unnecessary Operational Columns & Add Unique Trip ID
columns_to_drop = [
    "dispatching_base_num", "originating_base_num", "shared_request_flag", 
    "shared_match_flag", "access_a_ride_flag", "wav_request_flag", "wav_match_flag"
]
df_cleaned_cols = df_base_data.drop(*columns_to_drop).withColumn("trip_id", monotonically_increasing_id())

# 6. Impute Missing 'on_scene_datetime' with 'request_datetime'
df_imputed = df_cleaned_cols.withColumn(
    "on_scene_datetime",
    coalesce(col("on_scene_datetime"), col("request_datetime"))
)

# 7. Define Strict Data Quality Filtration Rules
valid_conditions = (
    col("hvfhs_license_num").isNotNull() &
    col("request_datetime").isNotNull() &
    col("pickup_datetime").isNotNull() &
    col("dropoff_datetime").isNotNull() &
    (col("request_datetime") <= col("pickup_datetime")) &
    (col("pickup_datetime") < col("dropoff_datetime")) &
    col("PULocationID").between(1, 265) &
    col("DOLocationID").between(1, 265) &
    (col("trip_time") > 0) &
    (col("trip_miles") >= 0.0) &
    (col("base_passenger_fare") >= 0.0) &
    (col("tolls") >= 0.0) &
    (col("bcf") >= 0.0) &
    (col("sales_tax") >= 0.0) &
    (col("congestion_surcharge") >= 0.0) &
    (col("airport_fee") >= 0.0) &
    (col("tips") >= 0.0) &
    (col("driver_pay") >= 0.0)
)

# 8. Split Data: Clean vs. Quarantine
df_clean = df_imputed.filter(valid_conditions)
df_bad_records = df_imputed.filter(~valid_conditions)

# 9. Write Bad Records to Quarantine Zone (Append Mode)
print("Writing invalid records to quarantine zone...")
df_bad_records.coalesce(4).write \
    .mode("append") \
    .parquet("hdfs://uber-hadoop-master:9000/data/quarantine/rides/")

# 10. Load Reference Zone Data & Perform Broadcast Spatial Joins
print("Loading zone reference data and performing broadcast joins...")
df_zones = spark.read.csv("hdfs://uber-hadoop-master:9000/data/reference/zone_centroids.csv", header=True, inferSchema=True)

df_silver_joined = df_clean.join(
    broadcast(df_zones.withColumnRenamed("LocationID", "PULocationID") \
                      .withColumnRenamed("lat", "start_lat") \
                      .withColumnRenamed("lon", "start_lon")),
    on="PULocationID",
    how="left"
).join(
    broadcast(df_zones.withColumnRenamed("LocationID", "DOLocationID") \
                      .withColumnRenamed("lat", "end_lat") \
                      .withColumnRenamed("lon", "end_lon")),
    on="DOLocationID",
    how="left"
)

# 11. Apply H3 Hashing to Coordinates
print("Computing H3 spatial hashes...")
df_silver_final = df_silver_joined \
    .withColumn("start_geo_hash", compute_h3(col("start_lat"), col("start_lon"))) \
    .withColumn("end_geo_hash", compute_h3(col("end_lat"), col("end_lon")))

# 12. Write Cleaned, Enriched Data to Silver Layer (Overwrite Mode)
print("Writing processed data to Silver layer...")
df_silver_final.coalesce(8).write \
    .mode("overwrite") \
    .parquet("hdfs://uber-hadoop-master:9000/data/silver/staging_rides_geo/")

print("Silver Layer pipeline execution completed successfully!")