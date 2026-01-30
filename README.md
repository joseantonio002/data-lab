# data-lab

This repo is my working notebook of programming assignments from a Master's in Data Engineering. Each top-level directory is a course, and each assignment folder contains its own `README.md` explaining goals, environment, key artifacts, and what I learned.

## Courses and assignments

### `business_intelligence`
- `business_intelligence/TITSA_modeling` - Data modeling and a Power BI dashboard for a public transport operator (TITSA): objectives -> CSFs -> indicators -> multidimensional model -> dashboard.

### `large_scale_data_processing`
- `large_scale_data_processing/1_deploy_hadoop` - Manual Hadoop 3 cluster deployment in Docker (HDFS + YARN), plus BackupNode, TimelineServer, and rack awareness.
- `large_scale_data_processing/2_hdfs` - HDFS access from Python via PyArrow (`filesystem_cat.py`, `copy_half_file.py`) and admin tasks (quotas, `fsck`, failure simulation and recovery).
- `large_scale_data_processing/3_mapreduce` - StackOverflow analytics with MapReduce (MRJob): sorting patterns, distributed Top-K, joins, co-occurrence, and multi-step pipelines.
- `large_scale_data_processing/4_spark` - PySpark scripts for StackOverflow analytics: Parquet transforms, joins, window functions, rankings, and year-over-year deltas.

### `large_scale_databases`
- `large_scale_databases/MySQL` - Load a StackOverflow SQL dump into MySQL and run analytical SQL (derived facts, window functions, integrity checks) in a Dockerized notebook stack.
- `large_scale_databases/MongoDB` - MongoDB aggregation pipelines over StackOverflow: derived collections, `$lookup`, `$unionWith`, and an API-backed weather + activity analysis.
- `large_scale_databases/Cassandra` - Cassandra data modeling from Parquet schemas, query-driven denormalization, and multinode ingestion/queries via CQL.
- `large_scale_databases/Neo4j` - Graph modeling and Cypher analytics in Neo4j: constraints, tag extraction, recommendations, and multi-criteria scoring.
- `large_scale_databases/delta_lake_spark` - Optional lakehouse work: Delta Lake tables on Spark, OPTIMIZE/ZORDER/VACUUM, and performance comparisons vs Iceberg/Parquet.

### `statistical_learning`
- `statistical_learning/1_logreg_lda_pcr_pls` - Logistic regression vs LDA for classification, and Ridge/Lasso/PCR/PLS for regression with multicollinearity.
- `statistical_learning/2_bagging_boosting_svm` - Random Forest vs gradient boosting vs SVM on the BRFSS diabetes dataset, with grid search and one-standard-error selection.
- `statistical_learning/3_deep_learning` - Feedforward neural nets for diabetes prediction (regularization, BatchNorm, dropout, early stopping) and comparison vs classical ML.

### `unstructured_information_technologies`
- Assignment 1 (`unstructured_information_technologies/scrapper.ipynb`) - Large-scale news scraping, normalization, Elasticsearch indexing, and lexical vs semantic retrieval.
- Assignment 2 (`unstructured_information_technologies/youtube.ipynb`) - YouTube Data API collection, BM25-based text classification, transformer sentiment, and semantic similarity clustering.
