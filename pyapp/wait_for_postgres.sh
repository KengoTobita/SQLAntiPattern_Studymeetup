#!/bin/bash
set -e

host="db"
db="ec1"
user="user"
password="pass"

echo "Waiting for PostgreSQL ($host) to be ready and database '$db' to be available..."

until PGPASSWORD=$password psql -h "$host" -U "$user" -d "$db" -c '\q' > /dev/null 2>&1; do
  echo "Still waiting for database '$db' to be ready..."
  sleep 2
done

echo "PostgreSQL is ready and database '$db' is available. Starting application..."
exec "$@"
