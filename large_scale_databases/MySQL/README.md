 # Large Scale Databases · MySQL assignment

 This directory holds the artifacts for the MySQL assignment of the Large Scale Databases course. The goal was to load the Spanish StackOverflow snapshot, explore its schema and quality, and use analytical SQL to surface insights that demonstrate understanding of large relational datasets.

 ## Assignment goals

 - Provision a reproducible MySQL + analysis environment that mirrors the lab setup described in the course.
 - Load the `stackoverflow.sql.gz` dump into MySQL and exercise the main relational entities (`Posts`, `Users`, `Comments`, `Votes`, `Tags`) while keeping an eye on referential integrity.
 - Build derived tables/facts that answer business-style questions about response times, prolific users, and post ownership using advanced SQL constructs.

 ## Key artifacts

 - `BDGE_Primera_Práctica.ipynb`: notebook that documents the SQL-driven exploration, data validation steps, and summarises findings with charts engines such as Matplotlib.
 - `docker-compose.yml` + `Makefile`: orchestrate the multi-service stack that powers the assignment (init container, MySQL, Jupyter notebook).
 - `scripts/{setup-mysql-data.sh,init-alpine-container.sh}`: helper scripts that download the dataset and keep the init container alive without manual intervention.
 - `data/`: hosts the downloaded `stackoverflow.sql.gz` dump and the `done` sentinel that signals completion to the Compose healthchecks.

 ## Reproducing the environment locally

 ```bash
 make up       # starts the init container, MySQL instance, and the notebook service
 make shell    # opens a shell inside the notebook container for ad-hoc work
 make logs     # tails the Docker logs when troubleshooting
 make down     # stops the stack when done
 ```

 The Makefile wraps `docker compose` while exporting the current user IDs so that the notebook service can write to the shared workspace without permission issues.

 ## Docker environment overview

 1. **init-db (Alpine) → mysql → notebook**: The init container runs `scripts/init-alpine-container.sh`, which delegates to `setup-mysql-data.sh` to download the compressed StackOverflow dump and place it in `data/`. Docker's `healthcheck` waits for the `done` file before allowing MySQL to start importing data, guaranteeing idempotent dataset provisioning without bloating the MySQL image.
 2. **MySQL service**: Uses the official `mysql:8` image with a bind mount from `./data/` into `/docker-entrypoint-initdb.d`, so the dump is executed exactly once during the initial startup. Healthchecks keep retries high because loading the full dataset can take time, and MySQL depends on `init-db` succeeding first.
 3. **Notebook service**: Based on `jupyter/scipy-notebook`, it exposes port `8888`, mounts the course workspace (`..:/home/jovyan/work/bdge`), and injects the `mysql` hostname into the environment so `%sql` magic can reach the database. Waiting on the MySQL healthcheck ensures the notebook only becomes usable after the data is available.

 This topology isolates data provisioning from the MySQL server for faster iterations: if the dump is already cached in `data/`, `init-db` exits quickly, MySQL skips re-importing, and analysts can jump straight into writing SQL.

 ## SQL features exercised in this assignment

 - **Bulk ingestion + schema validation** via the prepared SQL dump and running `EXPLAIN` on key joins to understand queries over the large `Posts` table.
 - **Derived tables and correlated subqueries** to combine information from `Posts`, `Users`, `Comments`, and `Votes` when building the `StackOverflowFacts` fact table.
 - **Aggregation + window functions** such as `COUNT`, `AVG`, `MIN`, and `PERCENT_RANK() OVER (ORDER BY AverageResponseTime ASC)` to score users by responsiveness and measure time-to-first-answer using `TIMEDIFF`.
 - **Conditional logic** using `CASE WHEN` and `COALESCE` to avoid `NULL`s in ratio calculations and to compute percentile-adjusted scores.
 - **Data quality checks** (e.g., `WHERE UserId NOT IN (SELECT Id FROM Users)`) to detect orphaned references before trusting the exported facts.
