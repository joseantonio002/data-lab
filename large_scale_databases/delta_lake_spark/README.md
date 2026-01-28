# Delta Lake + Apache Spark · Large Scale Databases

This assignment documents the optional Delta Lake + Spark work for the course. The provided notebook (`delta_lake_spark.ipynb`) walks through why Delta Lake matters for lakehouse architectures, how to configure Apache Spark for Delta tables, how to ingest StackOverflow into Delta, and how to measure the performance impact of OPTIMIZE/ZORDER/VACUUM. The closing section compares Spark + Delta against Trino + Iceberg and raw Parquet.

## Why Delta Lake?

- Delta Lake sits on top of your cheap object storage (S3, HDFS, ADLS, GCS) and adds table format guarantees, so the lake behaves more like a hardened warehouse: ACID transactions, schema enforcement/evolution, metadata/versioning (time travel) and concurrent read/write safety.
- Delta Lake is not a standalone service; instead you add the `delta-spark` dependencies (or leverage a managed runtime like Databricks) so that your processing engine understands the `_delta_log` behind every table.
- Spark is the processing engine here (PySpark in Colab), but the same principles apply to other runtimes (Flink, Trino, Trino, Presto, etc.).

## Environment and setup

1. Install PySpark & Delta Lake libraries in Colab:

   ```bash
   %pip install pyspark delta-spark
   ```

2. Create the `SparkSession` with Delta extensions and catalog so that `spark.read.format("delta")` and `spark.sql("SELECT * FROM delta.`path`")` work.

3. Spark cannot read remote HTTPS Parquet directly, so the notebook downloads the exported StackOverflow `Users.parquet`, `Posts.parquet`, etc., writes them to local storage, creates DataFrames via `spark.read.parquet(...)`, and writes the resulting tables with `df.write.format("delta").mode("overwrite").save("/content/Users")`.

4. Delta tables live in directories with data files (usually Parquet) plus a `_delta_log/` folder containing JSON commits and periodic checkpoints. Never read the directory as raw Parquet—Delta interprets the log to know which files are currently valid.

## Query workflow & Delta operations

1. **RQ1–RQ4**: run SQL workloads over the new Delta tables. Each query initially scans multiple Parquet files, so the notebook captures Spark UI metrics (number of files, scan time, wall time) for the baseline run.

2. **OPTIMIZE** compacts small files in Delta tables (bin-packing) so downstream queries read fewer input files and avoid Spark scheduling overhead.

3. **ZORDER BY** reorganizes storage on selective filter columns; the notebook ZORDERs `Posts` on `OwnerUserId` and other filters, enabling data skipping and reducing scan time from 976ms to 435ms for RQ1.

4. **VACUUM** removes stale Parquet files no longer referenced by the transaction log. It trims storage, but be cautious with the retention period because it permanently deletes history needed for time travel.

5. The notebook re-runs each RQ query after OPTIMIZE+ZORDER and records the Spark UI metrics again. For example, RQ1 shrinks from three scanned files to one, and total wall time drops from ~15s to ~8s because each query touches fewer files and benefits from clustered filters.

## Numerical insights for RQ1–RQ4

| Query | Scan files before | Scan files after | Example wall time before | after |
| --- | --- | --- | --- | --- |
| RQ1 | 3 files | 1 file | 15s | 8s |
| RQ2 | 3 files | 1 file | ~25s | ~10s |
| RQ3 | 3 files | 1 file | 25.5s | 10.6s |
| RQ4 | 3 files | 1 file | 26.8s | 17.3s |

(The notebook logs exact `spark.sql` output and CPU times; please refer to the cells for additional metrics.)

## Delta vs Iceberg vs raw Parquet

- **Common ground**: Delta Lake and Apache Iceberg both use Parquet for data files while layering transactional metadata (snapshots, manifests, `_delta_log` or Iceberg metadata files) to enable ACID, schema evolution, time travel, and safe updates/deletes.
- **Parquet-only** works for append-only, single-writer use cases, but once you need concurrency, CDC, merges, auditing, or governance, table formats pay off.
- **Spark + Delta Lake** excels in heavy ETL/feature engineering jobs, streaming + batch unification, and large-scale MERGE/UPDATE/DELETE pipelines. Delta is tightly coupled to Spark but also compatible with Trino, Flink, and managed offerings (Databricks, Microsoft Fabric, AWS Athena, etc.).
- **Trino + Iceberg** shines when the primary workload is ad-hoc SQL serving: many concurrent users, federated catalogs, and low-latency queries. Iceberg was built from day one with a strict separation between format and engine, so it integrates natively with Trino, Spark, Flink, Hive, and others without requiring a dedicated runtime.
- **Deployment styles**: Delta + Spark tends to favor a lakehouse where Spark is the central orchestrator (batch/stream/ML). Trino + Iceberg leans toward a decoupled architecture (storage + catalog + SQL engine). Each approach has trade-offs in governance, latency, and tooling.

## Key takeaways

1. I can configure PySpark to understand Delta Lake, manage the `_delta_log`, and write/read tables so that downstream queries just see consistent snapshots.
2. I have hands-on experience measuring the impact of Delta maintenance commands (OPTIMIZE+ZORDER) by comparing Spark UI plans and timings before/after compaction.
3. I can articulate when to use Delta Lake vs Iceberg vs raw Parquet, tying each option to real workloads (ETL-heavy Spark pipelines vs SQL-serving Trino clusters).
