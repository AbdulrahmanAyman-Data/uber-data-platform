# docker/spark/Dockerfile
#
# Adds an isolated Python 3.10 environment (via Miniconda) on top of the
# stock bde2020 Spark 3.3.0/Hadoop 3.3 image, and installs h3-py into it.
#
# WHY: bde2020/spark-master|worker:3.3.0-hadoop3.3 ships Python 3.7.10.
# h3-py v4 (the version with the latlng_to_cell() API) officially requires
# Python >=3.8 -- there is no prebuilt wheel for cp37, and pip refuses to
# even attempt a source build because of h3-py's own python_requires
# constraint. Installing build tools (cmake/make) would NOT have fixed
# this -- the Python version itself is the blocker.
#
# Built TWICE (once per BASE_IMAGE) from docker-compose.yml -- see the
# build.args section for uber-spark-master and uber-spark-worker.
ARG BASE_IMAGE=bde2020/spark-master:3.3.0-hadoop3.3
FROM ${BASE_IMAGE}

USER root

# --- Miniconda (self-contained Python distribution, doesn't depend on
# whatever Python packages this base image's OS repos happen to have) ---
RUN apk add --no-cache wget bzip2 ca-certificates

ENV CONDA_DIR=/opt/conda
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh && \
    bash /tmp/miniconda.sh -b -p ${CONDA_DIR} && \
    rm /tmp/miniconda.sh
ENV PATH=${CONDA_DIR}/bin:${PATH}

# --- Isolated env with Python 3.10 + h3 (prebuilt wheel, no compiler needed) ---
RUN conda create -y -n h3env python=3.10 && \
    ${CONDA_DIR}/envs/h3env/bin/pip install --no-cache-dir h3 && \
    conda clean -afy

# Tell Spark (driver AND every executor) to use this Python instead of the
# system Python 3.7 -- absolute paths, so it works with or without
# "conda activate" (which the base image's own startup scripts don't do).
ENV PYSPARK_PYTHON=${CONDA_DIR}/envs/h3env/bin/python
ENV PYSPARK_DRIVER_PYTHON=${CONDA_DIR}/envs/h3env/bin/python
