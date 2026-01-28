# MongoDB · Large Scale Databases

The second practice covers MongoDB aggregation on the StackOverflow dataset. `BDGE_Segunda_Practica.ipynb` contains every step: connecting via `AsyncMongoClient`, building derived collections, and executing the analytical pipelines requested in the course exercises.

## Services

- `mongo`: official MongoDB 8 container exposes port `27017` and provides a `mongosh`-compatible endpoint with a simple ping-based healthcheck.
- `notebook`: Jupyter SciPy image that mounts the repo and exports `DB_HOSTNAME=mongo` so `%async` pipelines target the right host.

## Aggregation exercises and learning highlights

1. **User ↔ Tag mappings (E1)**: the pipeline splits the CSV-style `Tags` string, unwinds the result, groups by `(user, tag)`, and finally uses `$arrayToObject` to generate a document summarising how many questions each user asked per tag. The reverse mapping (tag → users) uses the same stages plus `$out` to persist `users_per_tag` for reuse.
2. **StackOverflowFacts (E2)**: `StackOverflowFacts` is rebuilt with `$unionWith` to append `Posts`, `Comments`, `Votes`, and `Users` events into a single stream, mirroring the relational fact table from the previous SQL session. This reinforced how MongoDB handles `UNION`-style logic via `$unionWith` rather than literal SQL UNION.
3. **Query RQ3 (E3)**: while computing per-user answer ratios, we used `$cond` inside `$group` to count answers vs total posts and `$lookup` + `$unwind` to join Users with their Posts. `$lookup` taught how to mimic joins by projecting related arrays and then exploding them.
4. **Time-to-event averages (E4/E5)**: pipelines normalise `QuestionId`, aggregate to capture the earliest response/accepted response, filter with `$filter`, and compute averages via `$avg` + `$project`. The second pipeline even stores intermediate arrays (`answers`) and filters by `acceptedAnswerId` to end up with precise time deltas.
5. **Clima & StackOverflow (E6)**: the workbook fetches AEMET OpenData in 6-month chunks (due to API limits), uses checkpoint files to resume downloads, and aggregates weather with StackOverflow activity—respecting constraints such as `Score >= 0`, weekdays only, and excluding Spanish holidays. The same notebooks show how to persist the climate data locally and join it with Mongo data for correlation queries.
