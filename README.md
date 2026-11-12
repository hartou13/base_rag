# Base RAG API

A FastAPI backend for retrieval-augmented generation (RAG). Users sign up, create collections, upload documents into them, and ask questions answered only from the content of a collection.

To install and run the project, and to add a module, see [QUICKSTART.md](QUICKSTART.md).

## Stack

- **API:** FastAPI, served by uvicorn
- **Database:** MySQL through async SQLAlchemy (`aiomysql`), migrations with Alembic. All primary keys are uuid4 strings.
- **Auth:** JWT bearer tokens, checked by a global middleware. Tokens are stored in `users_active_token` so they can be revoked on logout.
- **Vectors:** Chroma on disk (cosine similarity), one Chroma collection per API collection
- **Models (Ollama):** embeddings from a local Ollama (`qwen3-embedding`), answers from Ollama Cloud (`gemma4`, falling back to `gemma4:31b`)
- **Files:** PDF (text layer), `.txt` and `.md`
- **Packages:** managed with `uv`

## How it works

**Collections:** each user owns their collections and can create, list and delete them. Another user gets a 404 on a collection that is not theirs.

**Indexing:** a user uploads files into a collection. Each file is saved to disk and registered in the database. Its text is read, cut into 800-character chunks with a 100-character overlap, and embedded. The chunks are stored in Chroma with the file id, filename and chunk index as metadata. Indexing runs inside the upload request.

**Deleting a file:** `DELETE /files/{file_id}` removes one file: its vectors in Chroma, its copy on disk and its database row. The rest of the collection is untouched.

**Sessions:** a session is a saved conversation, independent of any collection, managed with `/sessions` (create, list, get with messages, rename, delete). Every chat message is stored in the database.

**Chat:** the user sends a `session_id`, a `collection_id` and a question. The question is embedded, the 3 nearest chunks are retrieved, and the chat model is asked to answer using only those passages. The session's last messages (`CHAT_HISTORY_LIMIT`, default 20) are sent to the model first, so it remembers the conversation. Once the answer is complete, the question and answer are saved to the session. The response is a stream of events: the sources (filename, chunk text, distance), the answer tokens, then done.

Interactive API docs are at `/docs` when the server is running.

## Security

The full list is in [FEATURES.md](FEATURES.md). In short:

- **Prompt injection:** a system prompt carries the rules, and the question and every retrieved chunk are wrapped in `<question>` / `<passage>` tags as quoted data. Tags inside the text are neutralised. The question and each chunk go through the same heuristic scan: a flagged question gets a 400, a flagged chunk is dropped. A random canary in the system prompt detects leaks of the prompt in answers.
- **Signed downloads:** `GET /files/{id}/download` (owner only) returns a URL signed with HMAC over file id, user id and expiry, valid 5 minutes (optionally single-use). `GET /files/{id}/content` accepts a Bearer token or a valid signature. Files are stored under uuid names and the upload folder is never served statically.
- **Upload validation:** size limit, PDF page limit, type checked by magic bytes, path parts stripped from filenames, encrypted PDFs and PDFs with JavaScript rejected.
- **Output and logs:** answers are rendered as Markdown only, never raw HTML. Images and links to hosts outside the allowlist are removed. Logs redact secrets, questions and chunks go to a separate rotated audit file, and old log rows are purged.

Required setting: `FILE_URL_SECRET` (32+ characters). The API refuses to start without it. All settings are listed in `.env.example`.

## Tests

```bash
uv sync --group dev
pytest tests
```

The tests cover the pure security code (signed tokens, upload validation, prompt guard, markdown sanitizer, log redaction). They need no database and no Ollama.

## Roadmap

See [../plan.md](../plan.md) for the proof of concept and the planned improvements (reranking, better chunking, hybrid search).
