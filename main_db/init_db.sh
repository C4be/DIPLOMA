#!/bin/bash
set -e

echo "Распаковываем и загружаем демо-базу данных..."
gunzip -c /tmp/demo.sql.gz | psql -U postgres

echo "Демо-база успешно создана!"