# docker/nifi/Dockerfile
# Extends the base NiFi image with Python3 + GeoPandas/Shapely so that the
# NiFi flow can run scripts/compute_zone_geometries.py directly via an
# ExecuteStreamCommand processor, instead of that step being a manual
# local run.
FROM apache/nifi:1.25.0

USER root

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        python3-venv \
        gdal-bin \
        libgdal-dev \
        libgeos-dev \
        libproj-dev \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir \
        geopandas \
        pandas \
        shapely \
        h3

# Scripts get bind-mounted at runtime (see docker-compose.yml), not baked
# in here, so updating a script doesn't require rebuilding the image.

USER nifi
