# Architecture — Campus Knowledge Assistant

## 1. System architecture

```mermaid
flowchart TD
    A[React + Vite Frontend] -- HTTP/REST + JWT --> B[FastAPI Backend]
    B --> C[(MySQL / PostgreSQL)]
    B --> D[(Pinecone Vector DB)]
    B --> E[Gemini Embeddings]
    B --> F[Gemini LLM]
```

The frontend never talks to MySQL, Pinecone, or Gemini directly — every external call is proxied and authorized through the FastAPI backend. No API keys exist in frontend code or bundles.

## 2. Request flow (general)

```mermaid
sequenceDiagram
    participant U as Student/Admin (browser)
    participant F as React Frontend
    participant B as FastAPI Backend
    participant DB as MySQL

    U->>F: Interacts with UI
    F->>B: REST call with Authorization: Bearer <JWT>
    B->>B: Decode JWT, load user (get_current_user)
    B->>DB: Query/mutate via SQLAlchemy
    DB-->>B: Rows
    B-->>F: JSON response
    F-->>U: Rendered UI
```

## 3. Document ingestion flow

```mermaid
flowchart TD
    A[Admin uploads PDF] --> B[Validate: extension, MIME, size, non-empty]
    B --> C[Generate safe server-side filename]
    C --> D[Save file to uploads/, create Document row: status=UPLOADED]
    D --> E[Return 201 to admin immediately]
    D --> F[BackgroundTask starts]
    F --> G[status=PROCESSING]
    G --> H[Extract text per page - PyMuPDF]
    H -->|no text found| X[status=FAILED, store processing_error]
    H --> I[Clean text: whitespace/artifacts only]
    I --> J[Chunk text: CHUNK_SIZE / CHUNK_OVERLAP, page-tracked]
    J --> K[Generate embeddings for each chunk - Gemini]
    K --> L[Upsert vectors to Pinecone with metadata]
    L --> M[status=PROCESSED, store page_count/chunk_count]
```

Reprocessing follows the same flow but first deletes existing vectors for that `document_id` from Pinecone, so no duplicate/stale vectors are left behind. Deletion follows the mirror path: delete vectors first (abort on failure, no orphan vectors), then delete the DB row and the file from disk.

## 4. RAG (question-answering) flow

```mermaid
flowchart TD
    A[Student submits question] --> B[Validate: non-empty]
    B --> C[Embed question - Gemini]
    C --> D[Pinecone similarity_search, top_k=RAG_TOP_K]
    D --> E{Any match >= RAG_MIN_SCORE?}
    E -- No --> F["Return: could not find this information..."]
    E -- Yes --> G[Build context block from matched chunks]
    G --> H[Build history block: last CHAT_HISTORY_TURNS]
    H --> I[Construct prompt: SYSTEM + CONTEXT + HISTORY + QUESTION]
    I --> J[Call Gemini LLM, temperature=0.1]
    J --> K[Return answer + source list]
    K --> L[Persist USER + ASSISTANT messages, MessageSource rows]
```

Retrieved document text is always treated as **data**, never as instructions — the system prompt explicitly tells the LLM to ignore any embedded "instructions" found inside retrieved PDF content (see `app/rag/prompts.py`).

## 5. Authentication flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant B as Backend

    U->>F: Submits email/password
    F->>B: POST /api/auth/login
    B->>B: verify_password (bcrypt)
    B->>B: create_access_token (JWT: sub=user_id, role, exp)
    B-->>F: {access_token}
    F->>F: Store token in localStorage
    F->>B: Subsequent requests: Authorization: Bearer <token>
    B->>B: get_current_user decodes JWT, loads user from DB
    B->>B: require_admin checks role == ADMIN (admin routes only)
```

## 6. Database responsibilities

- Stores users, their roles, and hashed passwords
- Stores document metadata (title, category, status, uploader, page/chunk counts) — never the PDF binary or embeddings
- Stores conversations and messages (full chat history)
- Stores `MessageSource` rows linking each assistant message to the documents/pages it cited

## 7. Pinecone responsibilities

- Stores one vector per document chunk, namespaced by `PINECONE_NAMESPACE`
- Vector IDs are deterministic (`doc-{document_id}-chunk-{chunk_index}`), which makes reprocessing/deletion straightforward
- Metadata on each vector carries enough context (document_id, title, category, page_number, chunk text) to answer a query without a second database round-trip

## 8. LLM responsibilities

- Gemini embeddings (`text-embedding-004`) turn text into vectors for both indexing and querying
- Gemini chat model (`gemini-1.5-flash` by default) generates the final answer, constrained by the RAG system prompt to only use retrieved context and to say "I don't know" when context is insufficient
