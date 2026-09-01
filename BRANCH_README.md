# Branch: youssef-michael

## Overview
This branch contains updates for computing taxi zone centroids and enhancing database initialization scripts.

## Changes Made

### 1. Zone Centroids Computation
- **File**: `scripts/compute_zone_centroids.py`
  - New Python script that computes the geographic centroids for all NYC taxi zones
  - Uses geospatial data from the taxi zones shapefile located in `docker/spark/notebooks/taxi_zones/`
  - Leverages GeoPandas library for efficient geographic calculations

### 2. Zone Centroids Output
- **File**: `zone_centroids.csv`
  - Generated CSV file containing computed centroid coordinates (latitude/longitude) for each taxi zone
  - Serves as reference data for the platform

### 3. Database Initialization Updates
- **File**: `scripts/postgres/init-app-databases.sh`
  - Updated initialization script with enhanced database setup procedures
  
- **File**: `scripts/setup_hdfs_dirs.sh`
  - Modified HDFS directory setup with improved configurations

### 4. Jupyter Notebook
- **File**: `docker/spark/notebooks/Untitled.ipynb`
  - Added notebook for Spark exploration and analysis in the Docker environment

## Usage

To compute zone centroids:
```bash
python scripts/compute_zone_centroids.py
```

This will:
1. Read the taxi zones shapefile data
2. Calculate geographic centroids for each zone
3. Output results to `zone_centroids.csv`

## Dependencies
- GeoPandas
- Pandas
- Shapely (for geometric operations)

## Notes
- The zone centroids data enhances the platform's geographic analysis capabilities
- The database initialization scripts provide more robust setup procedures
