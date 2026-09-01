#!/bin/bash
set -e
set -u



function create_app_database() {
	local db=$1
	local user=$2
	local password=$3

	echo "Creating user '$user' and database '$db'"
	psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
	    CREATE USER "$user" WITH PASSWORD '$password';
	    CREATE DATABASE "$db" OWNER "$user";
	    GRANT ALL PRIVILEGES ON DATABASE "$db" TO "$user";
EOSQL
}

if [ -n "${POSTGRES_APPS:-}" ]; then
	echo "App databases requested: $POSTGRES_APPS"
	for entry in $(echo "$POSTGRES_APPS" | tr ',' ' '); do
		db=$(echo "$entry" | cut -d: -f1)
		user=$(echo "$entry" | cut -d: -f2)
		password=$(echo "$entry" | cut -d: -f3)
		create_app_database "$db" "$user" "$password"
	done
	echo "App databases created"
fi
