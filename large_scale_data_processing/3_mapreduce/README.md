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

## Evidence Placeholders (add images later)
- ![Ordered counts output placeholder](images/pr3_count_answers_ordered.png)
- ![Top-K heap logic placeholder](images/pr3_topk.png)
- ![Technology evolution trend placeholder](images/pr3_trends.png)

## Technologies & Theory in Action
- **MapReduce mechanics**: every script follows the mapper → combiner → reducer pattern from `p3.ipynb`. `so_count_answers_ordered.py` uses two `MRStep`s—first to aggregate by `ParentId`, then to funnel everything through a single key (`None`) for total ordering, illustrating how to force global ordering.
- **Distributed Top-K**: `so_count_answers_topk.py` minimizes shuffle volume by bucketizing `parent_id % num_buckets`, keeping per-reducer min-heaps, and merging them in a final step. This demonstrates scalable ranking versus sorting the full dataset.
- **Filtering & aggregation**: `so_bytagyear.py` parses CSV rows via `csv.reader`, extracts tags with regex, emits textual keys `(year,tag)` via `TextProtocol`, and relies on combiners to reduce shuffle pressure.
- **Map-side join**: `so_join.py` disambiguates records through `P|`/`U|` prefixes, groups by `OwnerUserId`, and pairs each question with the author’s reputation—showing how MapReduce performs joins without an external SQL engine.
- **Co-occurrence mining**: `so_tagconc.py` generates sorted tag pairs via `itertools.combinations`, directly applying association-measure theory in a MapReduce job.
- **Multi-step pipelines**: `so_technology_evolution.py` chains four steps to compute weighted activity per tag, monthly deltas, and final trend labels based on the average of the last six deltas, showcasing MRJob’s ability to orchestrate complex flows.

## Lessons Learned
Implementing the same analytics with different patterns (global ordering vs. Top-K, prefix-based joins, multi-step pipelines) clarified which design choices minimize data shuffles. Writing `tcdm_pr3.pdf` forced me to reason about key ordering and combiner benefits, making it easier to diagnose bottlenecks when scaling these jobs to larger datasets.
