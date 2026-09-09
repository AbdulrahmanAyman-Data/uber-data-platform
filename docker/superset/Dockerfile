FROM apache/superset:latest
USER root

RUN . /app/.venv/bin/activate && \
    uv pip install psycopg2-binary "trino[sqlalchemy]"

USER superset