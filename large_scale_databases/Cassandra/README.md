# Cassandra · Large Scale Databases

This folder documents the StackOverflow-driven Cassandra assignment for the course. The notebook `BDGE_tercera_practica.ipynb` walks through connecting to a multinode Cassandra cluster, deriving CQL schemas from Parquet metadata, and designing query-specific tables that let us answer analytical questions without joins.

## Services

- `cassandra1`, `cassandra2` (in `docker-compose.yml`): two Cassandra nodes joined via the `cassandra-net` network. Each node tunes `storage_port`, tombstone thresholds and batch limits via `sed` before starting so the cluster behaves more predictably for large loads.<br>- `notebook`: Jupyter SciPy image that mounts the repository and uses `AsyncCluster` to reach the nodes. The notebook waits for both Cassandra nodes to register before running queries.

## Modeling & ingestion highlights

- The dataset comes from the `bd2-data` release (Parquet files for Posts, Users, Tags, Comments, Votes). The notebook downloads the schemas in parallel and feeds them to a helper function that maps PyArrow types to Cassandra primitives and produces `CREATE TABLE` statements with carefully chosen partition and clustering keys.
- We denormalize the relational model into query tables: `posts_by_user`, `Questions`, `Answers`, `Tags`, `Users`, and a `UserActivity` fact table that stores aggregates such as answer counts, first/accepted-answer time gaps, etc. Each table sets `WITH compression = {'class': 'LZ4Compressor'}` and, where appropriate, clustering orders (`DESC` for timestamps) so read patterns stay efficient in Cassandra.
- Because Cassandra lacks joins/aggregations, the notebook explicitly splits questions from answers, uses wide primary keys (`(user_id, score)` + clustering columns), and materializes filtered views (e.g., `QuestionsWithUserNames`). The design also incorporates `COALESCE`/`CASE` logic inside PyArrow-derived schemas so client code can insert defensively.

## Queries & operational learnings

- The notebook detects the runtime via `DB_HOSTNAME`: it connects to a local single node when working locally but falls back to the `cassandra1`/`cassandra2` cluster when running through Docker, demonstrating resilience to different deployments.
- Connection logic uses the Python Cassandra driver with `Cluster` + `Session`, loops until the cluster responds, and prints `system.local` metadata to confirm the version and hosts. This reinforced the importance of health-checks and retry loops when bootstrapping a distributed store.
- We inspect the schema (`session.set_keyspace('stackoverflow')`) before creating tables using the generated CQL statements, then run sample `SELECT` queries to validate row counts, `MIN/MAX` of timestamps, and cross-check that `Answers` contain the expected `(question_id, answer_id)` composite key.
