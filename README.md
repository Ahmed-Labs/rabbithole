# RabbitHole

RabbitHole is a web app for **related-work exploration**: you pick a seed paper, and the system lays out its citation neighborhood as an interactive graph. The goal is not only to surface adjacent papers but to **rank and explain** how each one relates to the root, addressing the usual limitation of tools that stop at keywords, citations, or raw similarity without context.

Relevance uses two stages. **Quantitative scoring** combines cosine similarity on **SPECTER2** embeddings (full text is split into chunks, each chunk embedded, then **max-pooled** into one vector per paper) with publication-year similarity and a citation-count term; weights are fixed constants in [`relevance_scoring/constants.py`](relevance_scoring/constants.py). **Qualitative scoring** batches pairwise comparisons to **OpenAI** (`gpt-5-nano` in that file): each pair gets a 0-100-style score and a brief explanation. If an LLM score is present, `RelevanceScore.combined` in `relevance_scoring/relevance_scorer.py` merges it with the quantitative score using `LLM_SCORE_WEIGHT`. **Neo4j** holds papers, citations, and relevance edges; **`.embedding_cache`** stores embeddings keyed by paper id for reuse across requests.

## What the stack does

| Piece | Role |
|--------|------|
| **Flask** (`run.py`) | HTTP API under `/api`: search, async ingestion (`/embed`), task polling, and graph responses (filtering, on-request relevance fill-in, optional LLM task id, React Flow-ready payload). |
| **Celery** | Background work: citation ingestion + embeddings (`generate_embeddings_task`), batched LLM relevance updates (`generate_llm_score`). |
| **Redis** | Celery broker and result backend; separate logical DB for HTTP caching (`REDIS_CACHE_URL`). |
| **Neo4j** | Knowledge graph of papers, citations, and relevance edges. |
| **Vite + React** (`frontend/`) | React UI with React Flow. |

## Prerequisites

- **Docker** and Docker Compose
- **OpenAI API key**: required at startup (`LLMScorer` is constructed when Flask and Celery load)

## Quick start (Docker Compose)

1. **Environment**

   Copy the example env file and set your key:

   ```bash
   cp .env.example .env
   # Edit .env: set OPENAI_API_KEY
   ```

   Compose reads `OPENAI_API_KEY` from your host environment or from `.env` in the project root (Docker variable substitution).

2. **Start everything**

   ```bash
   docker compose up -d --build
   ```

3. **URLs**

   | Service | URL |
   |---------|-----|
   | React (Vite dev) | http://localhost:5173 |
   | Flask API | http://localhost:5000 |
   | Neo4j Browser | http://localhost:7474 (user `neo4j`, password `rabbithole`) |
   | Flower (Celery) | http://localhost:5555 |

## Environment variables

See [`.env.example`](.env.example) for a full list. Important ones:

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | Required for app/worker startup and LLM relevance scoring. |
| `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` | Neo4j Bolt auth. In Compose, `NEO4J_URI` is `bolt://neo4j:7687`. |
| `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` | Redis DBs `0` and `1` for Celery. |
| `REDIS_CACHE_URL` | Redis DB for `requests-cache`. **Must be set**; paper retrieval fails without it. |
| `REDIS_HOST` | Used where hostname resolution matters; Compose sets `redis`. |
| `FLASK_APP`, `FLASK_ENV`, `PORT`, `SECRET_KEY` | Flask runtime (see `.env.example`). |

Default Neo4j credentials in Compose match `.env.example`: user `neo4j`, password `rabbithole`.

## Paper ingestion pipeline

End-to-end flow when you **POST `/api/embed`** (or the UI’s “find related papers” action). The API returns a **task id** immediately; a Celery worker performs the heavy steps:

1. **Search**: text query against the paper catalog; only papers with a usable **open-access PDF** (`pdf_url`) are kept, so many hits are dropped.
2. **Citation graph**: Starting from the top search result, the worker expands **references** and **citations** recursively (`build_citation_graph`), bounded by `max_depth` and `max_references` / `max_per_level`.
3. **Persistence**: `KnowledgeGraphWriter` ensures the Neo4j schema and writes the graph.
4. **Embeddings**: `Embedder` runs **SPECTER2** (`allenai/specter2_base` + adapter) over paper text; PDFs are downloaded and text-extracted with **PyMuPDF** where needed. Embeddings are cached on disk under `.embedding_cache` by default.

### Interactive graph load (`GET /api/graph/<paper_id>`)

On each load, the handler applies depth and metadata filters, **reuses** stored relevance edges when present, and **synchronously** fills in missing pairwise scores from stored embeddings (`RelevanceScorer`). The payload is shaped for **React Flow** (`ReactFlowFormatter`). Edges that still need LLM scores enqueue a batched Celery job; the response may include a **`task_id`** to poll (`queue_llm=0` disables that). LLM outputs are merged using `LLM_SCORE_WEIGHT` in `constants.py`.

## REST API (all routes prefixed with `/api`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Liveness check. |
| GET | `/api/search?query=...` | Paper search (JSON list). |
| POST | `/api/embed` | Queue ingestion. Body: `query` (required), `max_depth` (default `1`), `max_references` (default `10`). Returns `task_id` and `202`. |
| GET | `/api/task-status/<task_id>` | Celery task state and result/error. |
| GET | `/api/graph/<paper_id>` | Filtered subgraph, on-request relevance fill-in, optional LLM task id; query params: `max_depth`, `min_year`, `max_year`, `min_citations`, `min_relevance`, `queue_llm` (default on). Response `data` is React Flow-compatible. |

### Example: enqueue ingestion and poll

```bash
TASK=$(curl -sS -X POST http://localhost:5000/api/embed \
  -H "Content-Type: application/json" \
  -d '{"query":"phasor","max_depth":1,"max_references":10}' | jq -r .task_id)

curl -sS "http://localhost:5000/api/task-status/$TASK" | jq .
```

When the task succeeds, the payload includes `root_paper`, `root_paper_title`, etc.

## Neo4j

Browser: http://localhost:7474. Example pattern:

```cypher
MATCH p=()-[r:RELEVANT_TO]->() RETURN p LIMIT 50
```

## Code quality

```bash
isort .
black .
```

## Repository layout (high level)

- `app/`: Flask API routes, Celery task definitions, graph query orchestration, relevance edge upserts, React Flow JSON formatting.
- `db/`: Neo4j client and graph read/write.
- `paper_retrieval/`: Catalog search, PDF text, citation expansion.
- `relevance_scoring/`: Embedder, embedding store, relevance + LLM scorers.
- `frontend/`: React + Vite app (see `frontend/README.md`).
