# Unstructured Information Technologies

Two complementary assignments explore text acquisition and search over the open web and YouTube. Each section below summarizes the scope, required artifacts, runtime setup, key technologies (with theory highlights), and the lessons that guided future improvements.

## Assignment 1 · `scrapper.ipynb` — Large-Scale News Scraping & Search

### Summary & Goals
The first notebook develops an end-to-end news pipeline: crawl 800+ economic articles through RSS, JSON-LD, and custom HTML spiders; normalize text metadata; index the corpus in Elasticsearch; then compare lexical search (BM25) with semantic retrieval (k-NN + hybrid ranking) and classical vectorization (TF/IDF). The deliverables are the crawled JSON collections, Elasticsearch indices (`indice_ej2.json`, `indice_ej3.json`), and exploratory analytics stored in the notebook.

### Supporting Files
- `scrapper.ipynb` – executable narrative that documents every crawler, index build, search experiment, and TF/IDF analysis.
- `rss/`, `json-ld/`, `tvcanaria/` – raw article dumps per acquisition strategy.
- `data/`, `json-ld/`, `rss/`, `tvcanaria/` – reused by the indexing and ML sections.
- `docker-compose.yml` – spins up Elasticsearch 8.12.1 + Kibana 8.12.1 for local experimentation.
- `embeddings-s-model.bin` – FastText Spanish embeddings required for vector comparisons and k-NN warm starts.
- `indice_ej2.json`, `indice_ej3.json`, `ElasticsearchWithCurl.txt` – exported indices and reference queries for validation.

### Runtime Environment
Run `docker compose up` in this folder to launch Elasticsearch/Kibana with security disabled for ease of use. Notebooks expect Python 3.12 with Scrapy, BeautifulSoup4, python-dateutil, sentence-transformers, scikit-learn, nltk, fasttext, pandas, matplotlib, seaborn, and the official `elasticsearch` client. These dependencies cover crawling, natural-language preprocessing, vector search, and visualization.

### Technologies & Theory Highlights
- **Structured & unstructured scraping.** Scrapy spiders illustrate why RSS and JSON-LD feeds (pre-structured XML/JSON) simplify extraction, while raw HTML requires DOM inspection and resilient selectors. Custom user-agents and pagination guards mitigate blocking.
- **Elasticsearch analyzers and mapping theory.** The notebook explains text analyzers (tokenizer + lowercase + `_spanish_` stopwords + light stemming), `keyword` vs. `text` vs. `date` fields, and why `_id` determinism avoids duplicates during bulk indexing.
- **Query DSL patterns.** Examples cover `bool` queries with `must/should/must_not`, operator-heavy `query_string`, ranged date filters, highlighting, fuzziness, and pagination. Comparisons clarify how BM25 scores relate to document term statistics.
- **Semantic search & hybrid ranking.** Sentence Transformers (`hiiamsid/sentence_similarity_spanish_es`) embed titles/contents into 768-d vectors stored as `dense_vector` fields using HNSW indexes. k-NN searches, hybrid lex/vec queries (boosted should clauses), and evaluation runs demonstrate how cosine similarity complements term matching.
- **Classical vectorization.** A final section revisits Bag-of-Words, CountVectorizer, TF, TF-IDF, Spanish stopwords, `min_df` filtering, and term frequency exploration to ground the modern methods in traditional IR theory.

### Lessons Learned
Mixing structured feeds with bespoke spiders reduces engineering overhead, but consistent normalization (dates, encodings, URL-based IDs) is essential before indexing. Hybrid IR that fuses analyzers, DSL filters, and dense embeddings recovers both literal and paraphrased evidence, while traditional TF/IDF explorations remain useful sanity checks when troubleshooting analyzer choices.

## Assignment 2 · `youtube.ipynb` — Text Mining the YouTube Ecosystem

### Summary & Goals
The second notebook focuses on API-driven acquisition and modeling. It automates the retrieval of 100 representative videos (per channel) for 30 Spanish-language channels across fitness, cooking, and science; builds channel-type classifiers from video descriptions; enriches comments with transformer-based sentiment; and clusters channels via semantic similarity. Deliverables include the processed datasets under `data/`, trained BM25-based classifiers, sentiment-enriched JSON exports (`*_apartado3`), and similarity visualizations.

### Supporting Files
- `youtube.ipynb` – main analysis containing API clients, sampling heuristics, ML training, sentiment inference, and similarity tooling.
- `data/fitness`, `data/cocina`, `data/ciencia` – JSON exports of the curated 100-video subsets per channel category.
- `data/fitness_apartado3`, `data/cocina_apartado3`, `data/ciencia_apartado3` – same datasets enriched with BETO sentiment tags for each comment.
- `BM25.py` – helper transformer (downloaded in-notebook) that implements BM25 weighting over scikit-learn sparse matrices.
- `embeddings-s-model.bin` – reused FastText Spanish embeddings for sentence-level similarity of channel descriptions.

### Runtime Environment
Requires Python 3.12 with `googleapiclient`, pandas, NumPy, scikit-learn, xgboost, matplotlib, seaborn, transformers (PyTorch backend), fasttext, tqdm, and nltk. A valid YouTube Data API v3 key must be set via `API_KEY`. GPU acceleration is optional but speeds up BETO inference for large comment sets.

### Technologies & Theory Highlights
- **YouTube Data API orchestration.** `googleapiclient` handles playlist, video, and comment endpoints. The notebook discusses `part` selections (`snippet`, `contentDetails`, `statistics`), quota-aware batching (50 playlist items per call, comment pagination), and heuristics that filter for informative videos (≥20 comments, ≥50-char descriptions, ≥5-minute duration).
- **Temporal sampling logic.** Per-channel video IDs are spread across uniform time bins to avoid clustering on one era, ensuring each 100-video sample captures the channel’s evolution.
- **Text classification via BM25 features.** Descriptions form a corpus vectorized with `CountVectorizer` + `BM25Transformer`. LinearSVC, RandomForestClassifier, and XGBoost classify channels into {ciencia, cocina, fitness}. Discussion covers BM25 theory, train/test splits (70/30 split by channel), and performance diagnostics (precision/recall tables, confusion matrices, systematic errors on “fitness”).
- **Sentiment analysis with transformers.** The BETO model (`finiteautomata/beto-sentiment-analysis`) tokenizes each comment (with 512-token truncation), predicts NEG/NEU/POS, and stores structured outputs—demonstrating contextual embeddings and inference pipelines.
- **Semantic similarity & visualization.** FastText sentence vectors summarize each channel’s descriptions. Cosine similarity matrices, heatmaps, PCA+t-SNE projections, and top-k neighbor lists surface clusters of related creators beyond manual labeling.

### Lessons Learned
API-centric pipelines need strict heuristics (quota limits, comment availability, duration thresholds) to deliver balanced datasets. BM25 features can outperform TF-IDF for multiclass description classification, yet class vocabularies still matter (“fitness” overlaps with “science”). Large-language models such as BETO simplify downstream sentiment tagging, and fastText-based similarity checks proved invaluable to sanity-check classifier labels and discover cross-domain creator affinities.
