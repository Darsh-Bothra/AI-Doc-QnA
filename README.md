# AI Doc QA

Backend for asking questions over uploaded documents. Users authenticate, upload PDFs, and the service extracts text, splits it into chunks, and stores those chunks for later retrieval.

Question answering and embeddings are not wired up yet. The current surface is auth, document CRUD, and ingestion.

## Stack

- Python 3.11+
- FastAPI and Uvicorn
- SQLAlchemy 2 (async) with PostgreSQL 17 via psycopg
- Alembic for migrations
- JWT access tokens (Bearer)
- Argon2 password hashing
- PyMuPDF / pymupdf4llm for PDF-to-markdown extraction

## Prerequisites

- [uv](https://docs.astral.sh/uv/)
- Docker (for PostgreSQL)

## Setup

```bash
git clone <repo-url>
cd ai-doc-qa
uv sync
docker compose up -d
```

Create a `.env` in the project root:

```env
POSTGRES_URL=postgresql+psycopg://ai_doc_qa:pg**ai**doc@localhost:5433/doc_db
JWT_SECRET=change-me
JWT_ALGO=HS256
```

The compose file maps Postgres to host port **5433** (`POSTGRES_USER=ai_doc_qa`, `POSTGRES_DB=doc_db`). Change the password in both `docker-compose.yaml` and `.env` if you are not using the local defaults.

Apply migrations:

```bash
uv run alembic upgrade head
```

Run the API:

```bash
uv run uvicorn ai_doc_qa.main:app --reload
```

Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) for the interactive OpenAPI UI.

`GET /health/db` checks that the app can talk to Postgres.

## API

Protected document routes expect `Authorization: Bearer <access_token>`.

### Auth

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/register` | Create a user (`email`, `password`) |
| `POST` | `/auth/login` | Return a JWT (`access_token`, `token_type`) |

Login and register use JSON bodies, not OAuth2 form fields.

### Documents

PDFs only, max **10 MB**. Files are stored under `uploaded_documents/` with a generated name; the original filename is kept on the `documents` row.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/documents/` | List the current user's documents |
| `GET` | `/documents/{document_id}` | Fetch one document owned by the current user |
| `POST` | `/documents/` | Upload a PDF, run ingestion, persist chunks |
| `DELETE` | `/documents/{document_id}` | Delete the row and the file on disk |

Document status values: `processing`, `completed`, `failed`. Upload currently leaves status as `processing` after chunks are saved.

## Ingestion

On `POST /documents/`:

1. Validate content type and size, write the file to disk, insert a `documents` row.
2. `PDFTextExtractor` converts the PDF to markdown with pymupdf4llm.
3. `StructureAwareChunker` splits on markdown headings (`#` … `######`).
4. `DocumentChunkRepository` writes `document_chunks` (`document_id`, `chunk_index`, `text`).

Chunks cascade-delete when a document is removed at the database level. `DELETE /documents/{id}` removes the document row and the file; ensure the chunk FK cascade is applied via migrations.

## Project layout

```
src/ai_doc_qa/
  main.py                 # FastAPI app
  api/routes/             # /auth, /documents
  db/models/              # User, Document, DocumentChunk
  schemas/                # Pydantic request/response models
  services/ingestion/     # extract → chunk → persist
  services/embedding/     # placeholder
  utils/                  # JWT and password hashing
migrations/               # Alembic
docker-compose.yaml       # local Postgres 17
uploaded_documents/       # user uploads (gitignored)
```

## License

Not specified.
