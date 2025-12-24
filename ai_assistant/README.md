

# Postgres развертывание базы данных

1. Запускаем контейнер:
   ```bash
   docker compose up -d
   ```
2. Запускаем скрипт для создания БД и ее заполнение:
   ```bash
    docker exec -i postgres-demo bash -c \
    "gunzip -c /dumps/demo-20250901-3m.sql.gz | psql -U postgres"
    ```