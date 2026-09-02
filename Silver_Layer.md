## 📋 Overview

The **Silver Layer** pipeline is a core data engineering component of the Uber NYC Ride Data Platform. Operating on raw ingestion data from the Bronze Layer, this stage cleans, standardizes, validates, and enriches approximately 80 million raw trip records. 

Key responsibilities of this layer include enforcing strict data quality contracts, isolating corrupted or anomalous records into an isolated **Quarantine Zone**, imputing missing operational timestamps, and performing spatial enrichment using **Uber's H3 geospatial indexing**.

---

## 🏗️ Architecture & Data Flow

Data flows through the pipeline using a distributed processing framework designed to optimize memory management and eliminate cluster network bottlenecks:

1. **Ingestion:** Reads raw Parquet files from the Bronze Layer storage (`/data/bronze/rides/`).
2. **Column Projection:** Drops unnecessary operational columns and generates a globally unique `trip_id` using `monotonically_increasing_id()`.
3. **Timestamp Imputation:** Automatically resolves missing non-critical operational timestamps (`on_scene_datetime`) using `request_datetime`.
4. **Data Quality Validation & Branching:** Evaluates records against strict business logic rules, splitting the stream into **Clean** (`df_clean`) and **Quarantine** (`df_bad_records`) datasets.
5. **Spatial Enrichment:** Joins clean records with geographic reference data using optimized **Broadcast Joins**, mapping coordinates to Resolution 9 hexagonal geohashes.
6. **Persistence:** Writes clean, enriched data to the Silver staging zone and routes bad historical records to the Quarantine audit zone.

---

## 🔍 Data Quality & Routing Rules

To ensure high-grade data for downstream analytics and machine learning, records are rigorously validated.

### 🚫 Quarantine Zone (`/data/quarantine/rides/`)
* **Mode:** Append
* **Criteria:** Any record failing the validation checks is isolated here for auditing.
* **Validation Rules:**
  * **Non-Null Checks:** `hvfhs_license_num`, `request_datetime`, `pickup_datetime`, and `dropoff_datetime` must exist.
  * **Chronological Order:** $request\_datetime \le pickup\_datetime$ and $pickup\_datetime < dropoff\_datetime$.
  * **Spatial Bounds:** Pickup (`PULocationID`) and Dropoff (`DOLocationID`) zone IDs must fall within valid official TLC limits (`1` to `265`).
  * **Metric Integrity:** Trip duration (`trip_time`) must be $> 0$. Financial metrics (fares, tolls, tips, surcharges) and distance (`trip_miles`) must be $\ge 0.0$.

### ✨ Silver Staging Zone (`/data/silver/staging_rides_geo/`)
* **Mode:** Overwrite
* **Criteria:** Records passing all validation rules.
* **Enrichment Details:**
  * **Imputation:** Missing `on_scene_datetime` fields are filled with `request_datetime`.
  * **Spatial Join:** Matched with `zone_centroids.csv` via a cluster-wide Broadcast Join to prevent network shuffling.
  * **H3 Hashing:** Converted via a custom UDF into **Resolution 9 H3 hex cells** (`start_geo_hash`, `end_geo_hash`) for advanced spatial aggregation.

---

## ⚙️ Technical Stack & Performance Optimizations

* **Distributed Compute:** Apache Spark (PySpark)
* **Storage Layer:** Hadoop Distributed File System (HDFS) via Docker containerization.
* **Security & Permissions:** Programmatic user impersonation (`os.environ["HADOOP_USER_NAME"] = "hdfs"`) to guarantee write access to cluster directories.
* **Memory Management:** 
  * Explicit shuffle partition tuning (`spark.sql.shuffle.partitions = 200`).
  * Output file coalescing (`.coalesce()`) to prevent Java Heap Space `OutOfMemoryError` failures during write operations.
  * Broadcast joins to eliminate cross-node network data movement for small reference files.

---

## 🚀 Running the Pipeline

To execute the Silver layer transformation script in your distributed environment:

```python
# Ensure your Hadoop environment variables and Spark session are active, then run:
python scripts ->  silver-layer.py