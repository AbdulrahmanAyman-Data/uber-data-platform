# Uber Data Platform: End-to-End Big Data Engineering Project

Welcome to the **Uber Data Platform** repository!  
This project demonstrates an end-to-end **Big Data Engineering and Analytics Platform** built to process large-scale ride-hailing data and transform raw trip records into clean, reliable, and analytics-ready data.

The platform follows a **Medallion Architecture (Bronze → Silver → Gold)** and combines data ingestion, distributed processing, data quality, orchestration, metadata management, SQL analytics, and visualization into one complete pipeline.

---

## 📖 Project Overview

This project was built to simulate a real-world **Data Engineering platform** for ride-hailing analytics.

The main objective was to take large volumes of raw trip data and transform them into business-ready datasets that can be queried and visualized efficiently.

### 🔹 Data Engineering Pipeline

1. **Bronze Layer**
   - Raw ride-hailing data ingestion.
   - Monthly NYC TLC High Volume For-Hire Vehicle (HVFHV) Parquet files.
   - Raw data is stored in HDFS without changing its original structure.

2. **Silver Layer**
   - Data cleaning and standardization.
   - Schema enforcement.
   - Null handling.
   - Data validation.
   - Deduplication.
   - Invalid records are moved to a quarantine layer.
   - Derived fields such as trip duration and date attributes are generated.

3. **Gold Layer**
   - Business-ready analytical data.
   - Kimball **Star Schema**.
   - Fact and dimension tables.
   - Partitioned fact table for better query performance.
   - Geospatial information added to taxi zones.

4. **Analytics & BI**
   - Trino provides distributed SQL access to the Gold Layer.
   - Apache Superset is used to build interactive dashboards and business insights.

---

## 🏗️ Data Architecture

The platform follows a complete data flow from raw ingestion to business intelligence:

![Data Architecture](docs/Architecture.png)

### Pipeline Flow

```text
NYC TLC Data
     │
     ▼
Apache NiFi
     │
     ▼
HDFS - Bronze
     │
     ▼
Apache Spark
     │
     ▼
HDFS - Silver
     │
     ▼
Apache Spark
     │
     ▼
HDFS - Gold
     │
     ▼
Hive Metastore
     │
     ▼
Trino
     │
     ▼
Apache Superset
     │
     ▼
Analytics & Dashboards
