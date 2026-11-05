#!/bin/sh
set -eu

alembic -c api/alembic.ini upgrade head
exec python3 api/server.py
