# Seed local MySQL data

Run all commands from the **project root, `team2_merlion_express/`**, which contains `docker-compose.yml`, `data/` and `scripts/`. If your terminal is currently inside `scripts/`, first run `cd ..`. The location of this guide does not change the commands' working directory.

The dump creates and selects `merlion_express`. **Re-importing replaces the tables defined in the dump.**

## Main option — Docker Compose

Start Docker Desktop. If another local MySQL server is using port 3306, stop it first or use the local MySQL alternative below. Then start the project's MySQL service from the project root:

```bash
docker compose up -d 
docker compose ps mysql
```

Wait until MySQL shows as healthy; rerun `docker compose ps mysql` to check. Set the data path and import using the command for your terminal. Compose reads `docker-compose.yml` from the project root; the SQL file is read from your computer through input redirection, so no SQL-file volume mount is needed.

**macOS — Terminal:**

```bash
DATA_PATH="$PWD/data/team2_merlion_express_package"
docker compose exec -T mysql mysql -uroot -pcapstone < "$DATA_PATH/sql/merlion_ops.sql"
```

**Windows — Command Prompt (CMD):**

```bat
set "DATA_PATH=%CD%\data\team2_merlion_express_package"
docker compose exec -T mysql mysql -uroot -pcapstone < "%DATA_PATH%\sql\merlion_ops.sql"
```

The service name `mysql`, root password `capstone` and host port `3306` match the project's `docker-compose.yml`. MySQL data persists in its `mysql_data` named volume. These commands run the MySQL client inside the container; you do not need a separately installed MySQL client for this option.

### Verify Docker import — macOS and Windows CMD

1. List the created tables:

   ```text
   docker compose exec -T mysql mysql -uroot -pcapstone -D merlion_express -e "SHOW TABLES;"
   ```

   Expect `drivers`, `orders` and `deliveries`.

2. Count rows in each table:

   ```text
   docker compose exec -T mysql mysql -uroot -pcapstone -D merlion_express -e "SELECT 'drivers' AS table_name, COUNT(*) AS row_count FROM drivers UNION ALL SELECT 'orders', COUNT(*) FROM orders UNION ALL SELECT 'deliveries', COUNT(*) FROM deliveries;"
   ```

## Alternative — Existing local MySQL

Requires MySQL 8 running locally, with `mysql` and `mysqladmin` available in your terminal. Enter your local MySQL password when prompted. Replace `root` if you use another user.

### macOS — Terminal

1. Set the data path:

   ```bash
   DATA_PATH="$PWD/data/team2_merlion_express_package"
   ```
2. Check MySQL is running:

   ```bash
   mysqladmin -h 127.0.0.1 -u root -p ping
   ```

   Expect `mysqld is alive`. If it cannot connect, start MySQL using your installation's service manager, then retry.

3. Import the SQL data:

   ```bash
   mysql -h 127.0.0.1 -u root -p < "$DATA_PATH/sql/merlion_ops.sql"
   ```

### Windows — Command Prompt (CMD)

Use Command Prompt for these commands; the import redirection below is not PowerShell syntax.

1. Set the data path:

   ```bat
   set "DATA_PATH=%CD%\data\team2_merlion_express_package"
   ```

2. Check MySQL is running:

   ```bat
   mysqladmin -h 127.0.0.1 -u root -p ping
   ```

   Expect `mysqld is alive`. If it cannot connect, open **Services**, start your MySQL service (commonly `MySQL80`), then retry.

3. Import the SQL data:

   ```bat
   mysql -h 127.0.0.1 -u root -p < "%DATA_PATH%\sql\merlion_ops.sql"
   ```

### Verify local import — macOS and Windows CMD

Enter your local MySQL password for each command. Replace `root` if you use another user.

1. List the created tables:

   ```text
   mysql -h 127.0.0.1 -u root -p -D merlion_express -e "SHOW TABLES;"
   ```

   Expect `drivers`, `orders` and `deliveries`.

2. Count rows in each table:

   ```text
   mysql -h 127.0.0.1 -u root -p -D merlion_express -e "SELECT 'drivers' AS table_name, COUNT(*) AS row_count FROM drivers UNION ALL SELECT 'orders', COUNT(*) FROM orders UNION ALL SELECT 'deliveries', COUNT(*) FROM deliveries;"
   ```

## Expected Data Counts

```text
+------------+-----------+
| table_name | row_count |
+------------+-----------+
| drivers    |        40 |
| orders     |     25833 |
| deliveries |     24802 |
+------------+-----------+
```