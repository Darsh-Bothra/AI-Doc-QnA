# AI Doc QA

A FastAPI backend for **question answering over uploaded PDFs**. Users register and log in, upload documents, and the service:

1. Extracts text from the PDF
2. Splits it into heading-aware chunks
3. Stores chunk text in PostgreSQL
4. Embeds those chunks with OpenAI and indexes them in Qdrant
5. Answers questions with retrieval-augmented generation (RAG)

Search and ask only work on documents whose status is `completed`.

For a full walkthrough of the stack, why each piece exists, and how ingestion/RAG fit together (including diagrams), see **[docs/tech-architecture.md](docs/tech-architecture.md)**. For what to build next, see **[docs/roadmap.md](docs/roadmap.md)**. To learn CI/CD on this repo (GitHub Actions, tests, then delivery), see **[docs/ci-cd.md](docs/ci-cd.md)**.

## Stack

- **Python 3.11+** (see `.python-version`)
- **FastAPI** and **Uvicorn**
- **SQLAlchemy 2** (async) with **PostgreSQL 17** via psycopg
- **Alembic** for migrations
- **Qdrant** for vector search
- **OpenAI** for embeddings (`text-embedding-3-small` by default) and answers (`gpt-4o-mini`)
- JWT access tokens (Bearer) and Argon2 password hashing
- **PyMuPDF / pymupdf4llm** for PDF-to-markdown extraction
- **uv** for dependency management

## Prerequisites

- [uv](https://docs.astral.sh/uv/)
- [Docker](https://docs.docker.com/get-docker/) and Docker Compose (Postgres + Qdrant)
- An [OpenAI API key](https://platform.openai.com/api-keys) (required for upload, search, and ask)

## Running the project

### 1. Clone and install dependencies

```bash
git clone <repo-url>
cd ai-doc-qa
uv sync
```

### 2. Start Postgres and Qdrant

```bash
docker compose up -d
```

Compose starts:

| Service  | Container             | Host ports   | Notes |
|----------|-----------------------|--------------|--------|
| Postgres | `ai_doc_qa_postgres`  | **5433** → 5432 | User `ai_doc_qa`, database `doc_db` |
| Qdrant   | `ai_doc_qa_qdrant`    | **6333** (HTTP), **6334** (gRPC) | Collection is created on first ingest |

Confirm they are up:

```bash
docker compose ps
```

### 3. Environment variables

Create a `.env` file in the project root (this file is gitignored):

```env
POSTGRES_URL=postgresql+psycopg://ai_doc_qa:pg**ai**doc@localhost:5433/doc_db
JWT_SECRET=change-me
JWT_ALGO=HS256

OPENAI_API_KEY=sk-...
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536

QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=document_chunks
```

If you change the Postgres password, update both `docker-compose.yaml` and `POSTGRES_URL`. `EMBEDDING_DIMENSIONS` must match the Qdrant collection vector size.

### 4. Apply database migrations

```bash
uv run alembic upgrade head
```

This creates the `users`, `documents`, and `document_chunks` tables.

### 5. Start the API

```bash
uv run uvicorn ai_doc_qa.main:app --reload
```

- API: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- Interactive OpenAPI docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- DB check: `GET /health/db`

Qdrant’s own UI is at [http://localhost:6333/dashboard](http://localhost:6333/dashboard) when the container is running.

### 6. Quick smoke test

1. `POST /auth/register` with `{ "email": "...", "password": "..." }`
2. `POST /auth/login` — copy `access_token`
3. `POST /documents/` as `multipart/form-data` with a PDF and header `Authorization: Bearer <access_token>`
4. When the document `status` is `completed`, `POST /documents/{id}/ask` with `{ "query": "..." }`

## How it works

```
PDF upload
  → extract markdown (pymupdf4llm)
  → split on markdown headings (# … ######)
  → save chunks in Postgres
  → embed with OpenAI
  → upsert vectors in Qdrant (payload: user_id, document_id, text)

Ask / search
  → embed the question
  → cosine search in Qdrant (filtered by user, optionally by document)
  → (ask only) send retrieved text + question to gpt-4o-mini
```

The LLM is instructed to answer **only** from retrieved context. If nothing relevant is found, it returns a fixed “not enough information” message.

## API

Protected document routes expect `Authorization: Bearer <access_token>`. Login and register use JSON bodies, not OAuth2 form fields.

### Auth

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/register` | Create a user (`email`, `password`) |
| `POST` | `/auth/login` | Return a JWT (`access_token`, `token_type`) |

### Documents

PDFs only, max **10 MB**. Files are stored under `uploaded_documents/` with a generated name; the original filename is kept on the `documents` row.

Document status: `processing`, `completed`, `failed`. After a successful ingest (Postgres + embeddings + Qdrant), status is set to `completed`.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/documents/` | List the current user's documents |
| `GET` | `/documents/{document_id}` | Fetch one document owned by the current user |
| `POST` | `/documents/` | Upload a PDF and run ingestion |
| `DELETE` | `/documents/{document_id}` | Delete the row and the file on disk |
| `POST` | `/documents/search` | Semantic search (`question`, optional `document_id`, `limit`) |
| `POST` | `/documents/{document_id}/ask` | RAG answer (`query`) for one completed document |

Search and ask return **409** if the document is not `completed`, and search returns **503** if retrieval fails.

### Other

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Simple liveness message |
| `GET` | `/health/db` | Runs `SELECT 1` against Postgres |

## Project layout

```
ai-doc-qa/
├── .github/workflows/           # GitHub Actions (see docs/ci-cd.md)
├── docs/
│   ├── tech-architecture.md     # Stack, architecture, and diagrams
│   ├── roadmap.md               # What to build next
│   └── ci-cd.md                 # CI/CD learning guide and resources
├── docker-compose.yaml          # Local Postgres 17 + Qdrant
├── alembic.ini                  # Alembic config (URL from POSTGRES_URL)
├── pyproject.toml               # Package metadata and dependencies
├── uv.lock                      # Locked dependency versions
├── .python-version              # Python 3.11
├── uploaded_documents/          # PDF uploads (gitignored except .gitkeep)
├── migrations/                  # Alembic migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       ├── 5638fdb2bfc8_create_users_table.py
│       ├── 4f7559a2c233_create_documents_table.py
│       └── 19b915a91cee_create_document_chunks.py
└── src/ai_doc_qa/
    ├── main.py                  # FastAPI app, health routes
    ├── api/
    │   ├── dependencies.py      # JWT → current user
    │   └── routes/
    │       ├── auth.py          # Register / login
    │       └── documents.py     # CRUD, search, ask
    ├── db/
    │   ├── db.py                # Async engine and session
    │   └── models/
    │       ├── base.py
    │       ├── user.py
    │       ├── document.py
    │       └── document_chunk.py
    ├── schemas/
    │   ├── user.py              # Auth request/response models
    │   └── document.py          # Document, search, and ask models
    ├── services/
    │   ├── ingestion/
    │   │   ├── extractor.py     # PDF → markdown
    │   │   ├── chunker.py       # Heading-aware splits
    │   │   ├── pipeline.py      # Extract → chunk
    │   │   ├── repository.py    # Persist chunks
    │   │   └── service.py       # Full ingest + embed + Qdrant
    │   ├── embedding/           # OpenAI embeddings
    │   ├── vector_store/        # Qdrant client
    │   ├── retrieval/           # Embed query + vector search
    │   ├── llm/                 # gpt-4o-mini generation
    │   └── rag/                 # Retrieve + prompt + LLM
    └── utils/
        ├── jwt.py               # Access tokens
        ├── security.py          # Argon2 hashing
        └── task.py              # Background ingestion + its own DB session
```

## License

Not specified.
