# Campus Knowledge Assistant

An AI-powered Retrieval-Augmented Generation (RAG) chatbot that answers student questions using official college documents (attendance rules, exam schedules, scholarships, hostel rules, placement guidelines, etc.) — grounded strictly in uploaded PDFs, with source citations, and a clear "I couldn't find this" fallback when information isn't available.

---

## 1. Features

- Student login/registration, JWT authentication, role-based access (STUDENT / ADMIN, extensible to FACULTY)
- Admin PDF upload with metadata (title, category, department, academic year)
- Background document processing: text extraction → cleaning → chunking → embeddings → Pinecone storage
- RAG chat: question → retrieval (with relevance threshold) → grounded LLM answer → source citations (document + page)
- Persistent conversations per student, with limited recent-history context for follow-up questions
- Admin dashboard: processing stats, reprocess, delete (with vector cleanup)
- Light/dark theme, clean non-generic UI

## 2. Architecture

See [`docs/architecture.md`](docs/architecture.md) for diagrams. In short:

```
React (Vite) ──HTTP/REST──> FastAPI ──> MySQL (metadata, chat, users)
                                 ├──> Pinecone (vector search)
                                 └──> Gemini (embeddings + LLM)
```

## 3. Technology stack

- **Backend:** Python, FastAPI, SQLAlchemy, Alembic, MySQL (Postgres-ready), JWT, bcrypt, PyMuPDF, LangChain, Pinecone, Gemini
- **Frontend:** React 18, Vite 4, React Router, Axios, plain CSS (CSS variables for theming)

## 4. Prerequisites

- Python 3.10.x (recommended for High Sierra — see note in `backend/requirements.txt`)
- Node.js 16.x
- MySQL 8.x running locally
- A Pinecone account + API key ([pinecone.io](https://www.pinecone.io))
- A Gemini API key ([Google AI Studio](https://aistudio.google.com))

## 5. Folder structure

```
campus-knowledge-assistant/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/        # config, security, dependencies
│   │   ├── db/           # engine, session, declarative base
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic request/response schemas
│   │   ├── api/routes/   # FastAPI routers
│   │   ├── services/     # business logic (auth, documents, chat, rag, vectors)
│   │   ├── rag/           # ingestion, embeddings, retriever, prompts
│   │   └── utils/
│   ├── alembic/
│   ├── uploads/
│   ├── tests/
│   ├── seed.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   └── src/
│       ├── pages/
│       ├── components/
│       ├── context/
│       ├── api/
│       └── styles/
├── docs/architecture.md
└── README.md
```

## 6. Environment variables

Copy `backend/.env.example` to `backend/.env` and fill in real values. Never commit `.env`.

Key variables: `DATABASE_URL`, `JWT_SECRET_KEY`, `PINECONE_API_KEY`/`PINECONE_INDEX_NAME`, `GEMINI_API_KEY`, `RAG_TOP_K`, `RAG_MIN_SCORE`, `CHUNK_SIZE`, `CHUNK_OVERLAP`, `FRONTEND_URL`.

## 7. MySQL setup

```sql
CREATE DATABASE campus_knowledge CHARACTER SET utf8mb4;
CREATE USER 'campus_user'@'localhost' IDENTIFIED BY 'campus_pass';
GRANT ALL PRIVILEGES ON campus_knowledge.* TO 'campus_user'@'localhost';
FLUSH PRIVILEGES;
```

Update `DATABASE_URL` in `.env` to match.

## 8. Pinecone setup

1. Create a Pinecone account and API key.
2. Set `PINECONE_API_KEY` in `.env`.
3. Leave `PINECONE_INDEX_NAME` as-is or choose your own — the backend auto-creates the serverless index on first startup if it doesn't exist (dimension = `EMBEDDING_DIMENSIONS`, default 768 for `text-embedding-004`).

## 9. Gemini / LLM setup

1. Get a Gemini API key from Google AI Studio.
2. Set `GEMINI_API_KEY` in `.env`.
3. `LLM_MODEL` defaults to `gemini-1.5-flash`; `EMBEDDING_MODEL` defaults to `models/text-embedding-004`.

## 10. Backend setup

```bash
cd backend
python3.10 -m venv venv
source venv/bin/activate        # macOS/Linux
pip install --break-system-packages -r requirements.txt   # or omit the flag inside a venv
cp .env.example .env            # then edit .env with real values
```

## 11. Alembic migrations

```bash
cd backend
alembic revision --autogenerate -m "initial migration"
alembic upgrade head
```

## 12. Frontend setup

```bash
cd frontend
npm install
cp .env.example .env    # if you create one; otherwise set VITE_API_BASE_URL directly
```

By default the frontend expects the backend at `http://localhost:8000` — override with `VITE_API_BASE_URL` in a `frontend/.env` file if needed.

## 13. Running the application

Backend:
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Frontend:
```bash
cd frontend
npm run dev
```

Visit `http://localhost:5173`.

## 14. API documentation

Once the backend is running: `http://localhost:8000/docs` (Swagger) or `http://localhost:8000/redoc`.

## 15. Default development users

Run the seed script to create local dev accounts (you set the passwords interactively — nothing is hardcoded):

```bash
cd backend
python seed.py
```

Creates `admin@example.com` (ADMIN) and `student@example.com` (STUDENT). **Development only — never reuse these in production.**

## 16. RAG workflow (plain-language summary)

1. Admin uploads a PDF → text is pulled out page by page.
2. The text is cleaned lightly and split into overlapping chunks (~1000 characters each).
3. Each chunk is turned into a vector (embedding) and stored in Pinecone along with which document/page it came from.
4. When a student asks a question, the question is also turned into a vector and compared against stored chunks.
5. Only chunks that are similar enough (above `RAG_MIN_SCORE`) are kept.
6. Those chunks are handed to the Gemini LLM along with strict instructions: answer only from this context, don't make things up, say so if the answer isn't there.
7. The answer is returned to the student along with which document(s)/page(s) it came from.

## 17. Troubleshooting

| Problem | Likely cause |
|---|---|
| `grpcio` fails to build on macOS | Old SDK on High Sierra — force a prebuilt wheel: `pip install --only-binary=:all: grpcio==1.67.1`, then pin that exact version in `requirements.txt` so a later `pip install` doesn't silently resolve to a newer source-only release |
| `pymupdf`/`PyMuPDFb` install fails ("no matching distribution") | Some `pymupdf` versions lack a prebuilt binary for older macOS — pin to a version confirmed to have one, e.g. `pymupdf==1.25.5` |
| `SSLCertVerificationError` on macOS when a Python script makes an HTTPS request | Python.org's installer doesn't wire up macOS's system certificate store — run `open "/Applications/Python 3.1x/Install Certificates.command"` once |
| `Can't connect to MySQL server` | MySQL not running, or `DATABASE_URL` credentials wrong |
| Document stuck on `FAILED` | Check `processing_error` field — usually a scanned/image-only PDF with no extractable text (OCR is out of scope) |
| Chatbot always says "couldn't find this information" | `RAG_MIN_SCORE` may be too high for your documents/questions — tune it down and re-test |
| `404 ... model is not found` from Gemini | Google deprecates/shuts down Gemini model IDs frequently (e.g. `text-embedding-004` and `gemini-1.5-flash` were both fully retired in 2026). This project defaults to `LLM_MODEL=gemini-flash-latest` (an alias Google keeps pointed at their current stable Flash model) and `EMBEDDING_MODEL=models/gemini-embedding-001` to reduce how often this breaks — if it still 404s, check `https://ai.google.dev/gemini-api/docs/models` for current model names |
| Pinecone `401 Unauthorized: Invalid API key` | Re-copy the key from the Pinecone dashboard using the copy icon (manual selection often truncates it); make sure there's no trailing space/quotes in `.env` |
| Pinecone dimension-mismatch errors | Make sure `PINECONE_INDEX_NAME` in `.env` points to a fresh index (not one reused from another project) — the backend auto-creates an index at `EMBEDDING_DIMENSIONS` (768) the first time it starts, but won't resize an existing index created with a different dimension |
| CORS error in browser console / login fails with `400` on the `OPTIONS` preflight | `FRONTEND_URL` in backend `.env` must match the frontend's actual origin *exactly*, including whether it's `localhost` or `127.0.0.1` — these are different origins to a browser even though they're the same machine. This project pins Vite to `host: 'localhost'` in `vite.config.js` and the backend additionally auto-allows both the `localhost` and `127.0.0.1` variants of `FRONTEND_URL` as a safety net |
| `ImportError: cannot import name 'User' from partially initialized module ...` (circular import) | Anything that imports `app.models.*` directly must first import `app.db.base` (which registers every model on `Base.metadata`). `app/main.py` and `seed.py` both do this already — if you add a new standalone script that touches models, add `from app.db import base` before importing any specific model |

## 18. Testing

```bash
cd backend
pytest tests/ -v
```

Tests use an in-memory SQLite database and mock the Pinecone/Gemini calls — no real credentials or network calls required to run the suite.

## 19. Future improvements

- FACULTY role
- DOCX/PPTX support, OCR for scanned PDFs
- Object storage (S3-compatible) instead of local `uploads/`
- Rate limiting
- Streaming LLM responses in the chat UI

## 20. Out of scope (by design)

Payments, notifications, mobile app, voice assistant, multi-agent architectures, Kafka/Redis/Celery/Kubernetes, microservices — kept out to preserve a clean, understandable monolith appropriate for a college minor project.
