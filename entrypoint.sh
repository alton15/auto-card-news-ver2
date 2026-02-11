#!/bin/sh
set -e

SEED_DIR="/seed"
DATA_DIR="/home/cardnews/.card-news"
SEED_FILES="publish_history.json threads_token.json"

for file in $SEED_FILES; do
    if [ -f "$SEED_DIR/$file" ] && [ ! -f "$DATA_DIR/$file" ]; then
        cp "$SEED_DIR/$file" "$DATA_DIR/$file"
        echo "Seeded $file from $SEED_DIR to $DATA_DIR"
    fi
done

exec "$@"
