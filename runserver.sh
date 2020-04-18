#!/bin/bash

set -e

until ./wait-for-it.sh "$DB_HOST_PORT"; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - executing command"

echo "running ----> app ---> main.py".

servercmd='gunicorn --bind 0.0.0.0:5000 main:app'

$servercmd
