#!/bin/bash

# Копируем архив и скрипт в контейнер
docker cp backup/demo-20250901-3m.sql.gz postgres_demo:/tmp/demo.sql.gz
docker cp init_db.sh postgres_demo:/tmp/init_db.sh

# Даем права на выполнение
docker exec postgres_demo chmod +x /tmp/init_db.sh

# Запускаем скрипт
docker exec postgres_demo /tmp/init_db.sh