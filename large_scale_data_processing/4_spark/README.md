# Practice 4 · Programming with Apache Spark (PySpark)

## Summary & Goals
- Following `Pr_4_Programacion_en_Apache_PySpark.ipynb`, I produced four `spark-submit`-ready scripts (`ej1.py`–`ej4.py`) and documented their execution in `tcdm_pr4.pdf`.
- **Exercise 1** generated `dfRespuestas.parquet` and `dfPreguntas.parquet`, condensing answers per question and extracting `QuestionId`, `OwnerUserId`, and year.
- **Exercise 2** combined those Parquet files with `Users.parquet` and `Comments.parquet` to compute per-user/per-year metrics (question counts, total answers received, total comments, average and max answers), exported as `resultado_e2.csv`.
- **Exercise 3** exploded tags from `Posts.parquet`, joined with Exercise 1 outputs, and ranked questions per tag/year (`resultado_e3.csv`) using window functions.
- **Exercise 4** counted questions per user/tag/year and computed year-over-year deltas via `lag`, storing the result in `resultado_e4.csv`.

## Supporting Files
- `Pr_4_Programacion_en_Apache_PySpark.ipynb`: exercise descriptions, requirements, and sample commands.
- `tcdm_pr4.pdf`: evidence with screenshots of the scripts running and artifacts being generated inside the requested environment.
- Scripts:
  - `ej1.py`: reads `Posts.parquet`, implements `n_answers`, `question_info`, and `write_single_parquet`.
  - `ej2.py`: aggregates by user/year and exports a single CSV.
  - `ej3.py`: ranks by tag/year using tag filters and CSV helpers.
  - `ej4.py`: counts by user/tag/year and computes deltas using windows.
- Derived data: `dfRespuestas.parquet`, `dfPreguntas.parquet`, `resultado_e{2,3,4}.csv` (each produced as a single file via temporary directories).

## Runtime Environment
- **Spark local mode**: executed with `spark-submit --master 'local[*]' --driver-memory 4g ...`; PySpark 3.5.3 was selected to match the available Java version (as noted in the PDF).
- **Parameterized execution**: every script validates `sys.argv` for in/out paths (e.g., `spark-submit ... ej3.py dfRespuestas.parquet dfPreguntas.parquet Posts.parquet python,java out.csv`).
- **Single-file outputs**: `write_single_parquet` and `write_single_csv` write to a temporary directory with `coalesce(1)`, rename `part-*.parquet/csv` to the requested filename, and clean `_SUCCESS`/`.crc` leftovers.
- **Data**: original Parquet datasets (`Posts`, `Users`, `Comments`) come from GitHub Releases; intermediates live alongside the scripts for reuse in later exercises.

## Evidence Placeholders (add images later)
- ![Spark job execution placeholder](images/pr4_execution.png)
- ![Ranking output placeholder](images/pr4_ranking.png)
- ![YoY delta output placeholder](images/pr4_deltas.png)

## Technologies & Theory in Action
- **Apache Spark DAGs**: each script builds a `SparkSession`, applies DataFrame transformations (`filter`, `select`, `groupBy`, `agg`, `join`), and defers actions (`write`) until the end, benefiting from Catalyst optimizations and lazy evaluation.
- **DataFrame API vs. SQL**: high-level functions (`F.col`, `F.count`, `F.date_format`, `F.split`, `F.coalesce`) keep the code declarative while generating efficient physical plans; Exercise 1’s gzipped Parquet output shows Spark’s tight integration with columnar formats.
- **Window functions**: Exercise 3 defines `Window.partitionBy("Tag","Año").orderBy(...)` with `row_number` for rankings, while Exercise 4 uses `lag` to compute year-over-year differences—demonstrating Spark’s ability to handle temporal analytics without manual loops.
- **Complex data handling**: tag strings like `<python><spark>` are normalized via `regexp_replace`, converted to arrays with `split`, intersected with study lists via `array_intersect`, deduplicated with `array_distinct`, and exploded, highlighting Spark’s strength with nested data.
- **Cross-dataset joins**: Exercise 2 joins `dfPreguntas`, `dfRespuestas`, `Users`, and `Comments`, showing how Spark leverages existing partitions to calculate composite metrics (sums, averages, maximums) at scale.

## Lessons Learned
This practice underscored how expressive the DataFrame API is: complex pipelines (tag/year rankings, YoY deltas) boil down to a handful of transformations, and local Spark UIs make validation quick. Perfecting the single-file writers was essential for meeting the submission rules and for understanding why Spark normally emits multiple `part` files per write.
