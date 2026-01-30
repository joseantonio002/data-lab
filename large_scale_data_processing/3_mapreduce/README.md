# Practice 3 · StackOverflow Analytics with MapReduce (MRJob)

## Summary & Goals
- Prepared `Posts.csv` and `Users.csv` via `descarga.py`/`p3.ipynb`, set up `mrjob` inside the `namenode` container, and verified execution both locally (`-r inline`) and on YARN (`-r hadoop`).
- Implemented the `so_count_answers*.py` family, showcasing simple counts, two-step global sorting, and distributed Top-K through deterministic buckets.
- Built additional exercises (`so_bytagyear.py`, `so_join.py`, `so_tagconc.py`, `so_technology_evolution.py`) covering tag/year filtering, dataset joins, tag co-occurrence, and multi-step pipelines to study technology trends.
- Captured outputs and CLI runs in `tcdm_pr3.pdf`, explaining the mapper/combiner/reducer flow for each script.

## Supporting Files
- `p3.ipynb`: practice specification, download instructions, and exercise requirements.
- `tcdm_pr3.pdf`: report with theoretical explanations, step diagrams, key topology sketches, and sample outputs.
- `requirements.txt`: Python dependencies for `mrjob`, `pandas`, etc.
- Source scripts:
  - `descarga.py`: downloads and extracts the StackOverflow CSVs.
  - `so_count_answers.py`, `so_count_answers_ordered.py`, `so_count_answers_topk.py`: response-count variants.
  - `so_bytagyear.py`: counts questions by year/tag.
  - `so_join.py`: map-side join between prefixed Posts (`P|`) and Users (`U|`).
  - `so_tagconc.py`: tag co-occurrence counts.
  - `so_technology_evolution.py`: four-step pipeline (join, monthly aggregation, deltas, CRECIMIENTO/DECLIVE/ESTABLE classification).

## Runtime Environment
- **`namenode` container (`luser`)**: install requirements and run jobs either locally or via Hadoop using `-r hadoop` with `hdfs://namenode:9000/...` inputs.
- **`.venv` virtual environment**: isolates Python dependencies required by `mrjob`.
- **Data**: `Posts.csv` and `Users.csv` are downloaded with `wget`, optionally prefixed (`sed 's/^/P|/'`) for join exercises, and uploaded to `/user/luser` via `hdfs dfs -put` when running on the cluster.
- **Execution**: scripts can run locally for debugging (`python3 so_count_answers.py Posts.csv > ...`) or inside Hadoop (`python3 so_count_answers.py -r hadoop hdfs://namenode:9000/...`). Screenshots of both paths live in the PDF.

## Mapreduce fundamentals

MapReduce is a **data-parallel programming model** designed for scalable and fault-tolerant processing on large clusters built from commodity hardware. It was popularized by **Apache Hadoop** and is especially suited for batch analytics over very large datasets stored in distributed file systems.

The model is inspired by **functional programming**, specifically the abstract operations *map* and *reduce*:

* **Map** applies a function independently to each input element, enabling massive parallelism.
* **Reduce** aggregates all values associated with the same key using an associative and commutative operation (e.g., sum, max).

In practice, MapReduce works entirely with **key–value pairs**.

### Core programming model

* **Map function**
  `map(K1, V1) → list(K2, V2)`
  Transforms input records into intermediate key–value pairs.

The type and meaning of the input key–value pair (K1, V1) are not chosen by the programmer, but are defined by the MapReduce framework and the input format being used. The framework is responsible for reading the raw data (files, blocks, records) and converting it into (K1, V1) pairs that are passed to the mapper.

In other words, the mapper never reads files directly; it only processes the logical records produced by the input format.

For example, text file input (default case)

Each line of the file is treated as one record:

K1: byte offset of the line in the file

V1: contents of the line (string)

* **Reduce function**
  `reduce(K2, list(V2)) → (K3, V3)`
  Combines all values associated with a key into a (usually single) output value.

A classic example is **word count**, where the mapper emits `(word, 1)` and the reducer sums the counts per word.

### Execution pipeline

Each MapReduce step follows a fixed execution pattern:

**Map → Combiner (optional) → Shuffle & Sort → Reduce**

The **shuffle & sort** phase is fully managed by the framework and is central to MapReduce:

* Intermediate `(key, value)` pairs are **partitioned** so that all values for the same key go to the same reducer.
* Keys are **grouped and sorted** before being delivered to reducers.
* Each reducer receives data as `(key, list_of_values)` and processes keys in sorted order.

A fundamental guarantee of MapReduce is that **all values for a given key are always processed by the same reducer**, which makes correct aggregation possible.

### Distributed sorting

MapReduce can perform **global distributed sorting** without explicitly coding a sorting algorithm:

* Mappers emit `(key, value)` pairs.
* Reducers use an identity reduce function.
* A custom partitioner assigns **ranges of keys** to reducers such that if `k1 < k2`, then `partition(k1) ≤ partition(k2)`.

By concatenating reducer outputs in order, the final result is globally sorted. This idea is used in multi-step jobs that require total ordering.

### Data storage and splits

MapReduce relies on a **distributed file system** (such as HDFS):

* Files are split into large **blocks** (typically 64–128 MB).
* Blocks are replicated across nodes for fault tolerance.

During job execution:

* Input data is divided into **logical splits**.
* Each split is processed by one **map task**.
* Splits often align with HDFS blocks, but they are conceptually different (logical vs. physical).

Map tasks are scheduled close to where the data lives, exploiting **data locality** and reducing network traffic.

### Reduce phase and output

* Reducers receive grouped and sorted data.
* Final outputs are written to the distributed file system.
* Each reducer produces **one output file**, so the number of reducers determines the number of result files.

### Parallelism and processing elements

Clusters expose **Processing Elements (PEs)** (CPU cores or execution slots).

* A job defines **M map tasks** and **R reduce tasks**.
* Typically:

  * `M` ≈ number of input splits
  * `R < M`, since reducers are more resource-intensive
* Choosing `M + R` much larger than the number of PEs improves load balancing and fault tolerance.

### Fault tolerance

MapReduce is designed to tolerate failures automatically:

* Workers send **heartbeats** to the master.
* Failed tasks are **re-executed** on other nodes.
* If a node crashes, all its tasks are relaunched elsewhere.
* **Speculative execution** mitigates slow (“straggler”) tasks by running duplicate copies and keeping the fastest result.

This behavior is essential in large clusters, where hardware and network issues are common.

### Optimizations: combiners and partitioners

**Combiner**

* A local aggregation step executed after the map phase.
* Reduces the amount of data sent during shuffle.
* Safe only when the reduce operation is **associative and commutative**.
* Often uses the same logic as the reducer.

**Partitioner**

* Default partitioner: `hash(key) mod R`
* Guarantees that identical keys go to the same reducer and usually balances load.
* Custom partitioners are useful when data must be grouped by domain-specific criteria (e.g., all URLs from the same host).

## Technologies & Theory in Action
- **MapReduce mechanics**: every script follows the mapper → combiner → reducer pattern from `p3.ipynb`. `so_count_answers_ordered.py` uses two `MRStep`s—first to aggregate by `ParentId`, then to funnel everything through a single key (`None`) for total ordering, illustrating how to force global ordering.
- **Distributed Top-K**: `so_count_answers_topk.py` minimizes shuffle volume by bucketizing `parent_id % num_buckets`, keeping per-reducer min-heaps, and merging them in a final step. This demonstrates scalable ranking versus sorting the full dataset.
- **Filtering & aggregation**: `so_bytagyear.py` parses CSV rows via `csv.reader`, extracts tags with regex, emits textual keys `(year,tag)` via `TextProtocol`, and relies on combiners to reduce shuffle pressure.
- **Map-side join**: `so_join.py` disambiguates records through `P|`/`U|` prefixes, groups by `OwnerUserId`, and pairs each question with the author’s reputation—showing how MapReduce performs joins without an external SQL engine.
- **Co-occurrence mining**: `so_tagconc.py` generates sorted tag pairs via `itertools.combinations`, directly applying association-measure theory in a MapReduce job.
- **Multi-step pipelines**: `so_technology_evolution.py` chains four steps to compute weighted activity per tag, monthly deltas, and final trend labels based on the average of the last six deltas, showcasing MRJob’s ability to orchestrate complex flows.

## Lessons Learned
Implementing the same analytics with different patterns (global ordering vs. Top-K, prefix-based joins, multi-step pipelines) clarified which design choices minimize data shuffles. Writing `tcdm_pr3.pdf` forced me to reason about key ordering and combiner benefits, making it easier to diagnose bottlenecks when scaling these jobs to larger datasets.
