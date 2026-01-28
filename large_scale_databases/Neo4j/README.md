# Neo4j · Large Scale Databases

This folder captures the fourth practice, where I ingest StackOverflow data into Neo4j, model the user/tag/post graph, and execute rich Cypher analytics. `BDGE_cuarta_practica.ipynb` contains the asynchronous driver wiring, constraint creation, DuckDB-powered Parquet loads, and every requested query.

## Services

- `neo4j`: official Neo4j latest image with Bolt + HTTP ports exposed. The container exposes 7474/7687, enables a larger heap (6 GB) and disables authentication for simplicity while healthchecks probe via HTTP.
- `notebook`: SciPy Jupyter image that mounts the repo, exports `DB_HOSTNAME=neo4j`, and runs the Python driver (`AsyncGraphDatabase`) to issue Cypher.

## Data pipeline & graph modeling

- The notebook uses `AsyncGraphDatabase.driver` to open a Bolt connection and then builds constraints for `User.Id`, `Post.Id`, and `Comment.Id`. These constraints create automatic indexes and keep `MERGE`/`MATCH` fast.
- Tags are extracted from the raw `<tag1><tag2>` strings by replacing `><` with commas, stripping `<`/`>`, splitting into a list, and `UNWIND`ing the result. For each tag we `MERGE` a `:Tag` node and create bidirectional `:TAGGED_WITH` / `:TAGS` edges so both traversals run smoothly.
- DuckDB reads the Parquet releases (`Users.parquet`, `Comments.parquet`, etc.) and feeds them into the helper `load_dataframe_neo4j`. For users we customize the Cypher to `MERGE` on `Id` (not `CREATE`) so loading new properties simply updates existing nodes. Comments use the standard loader, and subsequent Cypher queries stitch `User-[:COMMENTED]->(Comment)-[:ON]->(Post)`.

## Analytical Cypher patterns used

- `COLLECT` + `DISTINCT` gather per-user tag lists (matching `:Question` via `:Tag`). This materialised view helps with follow-up exercises (`:INTERESTED_IN` relationships).<br>- `MERGE` on `(u)-[:INTERESTED_IN]->(t)` ensures idempotent relationships derived from user questions, enabling friend/tag recommendations later.<br>- Recommendations: `MATCH (u)-[:RECIPROCATE]->(u2)-[:INTERESTED_IN]->(t)` filters tags the base user does not already follow, counts interested friends, and orders tags by popularity. This pattern demonstrates how graph traversals capture social influence. <br>- Expert detection uses `CALL { ... } UNION ALL` subqueries to aggregate answers and questions per tag, sums the counts, and stores the score as node properties. Aggregating `:RECIPROCATE` degrees and comment cascades (via additional MATCHes) completes the multi-criteria scoring pipeline.<br>- Paths/graph algorithms: a query finds user pairs connected by up to 3 `:RECIPROCATE` hops, filters on shared tags, and sorts by common interests/distance, showing how path length and shared metadata can inform networking insights.<br>
