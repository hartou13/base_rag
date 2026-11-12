# Features

A complete list of what the Base RAG API and its frontend do. Settings named here are environment variables (see `.env.example` and [QUICKSTART.md](QUICKSTART.md)).

## 1. Accounts and authentication

- Sign up and log in with email and password. Passwords are hashed with bcrypt.
- JWT bearer tokens, checked by a global middleware on every route except `/auth/login`, `/auth/sign-up` and `/health-check`.
- Tokens are stored in `users_active_token`, so logging out revokes them.
- The current user id is available to routers through `get_current_user`.
- Login, logout, registration and API key regeneration are recorded in the `logs` table.

## 2. Collections

- Create, list and delete collections. Each belongs to one user.
- Another user's collection returns 404, not 403, so its existence is not revealed.
- Deleting a collection removes its vectors, its uploaded files and its database rows.

## 3. Documents

- Upload one or several files into a collection: PDF (text layer), `.txt` and `.md`.
- Each file is stored, registered, read, split into 800-character chunks with a 100-character overlap, embedded and stored in Chroma.
- File status is tracked: `indexing`, `ready` or `failed`, with the error message.
- Re-index a file, or delete one file (vectors, disk copy and row) without touching the rest of the collection.
- View a file in a new tab (owner, Bearer token) or download it through a signed URL.

## 4. Sessions and chat

- Sessions are saved conversations, independent of any collection: create, list, open with messages, rename, delete.
- Chat takes a session, a collection and a question. The 3 nearest chunks are retrieved and the model answers from them only.
- The last `CHAT_HISTORY_LIMIT` messages (default 20) are sent to the model, so it remembers the conversation.
- The answer streams as server-sent events: `sources`, then `token` events, then `done` (or `error`).
- A turn is saved only after the answer is complete, so history never holds an unanswered question.
- The interface shows the answer as Markdown with expandable source excerpts.

## 5. Model providers

- Embeddings and chat sit behind provider interfaces, so another provider can be added without touching the pipeline.
- Ollama is the default: local embeddings, Ollama Cloud for answers, with a fallback chat model when the first is not found.

## 6. Security

### 6.1 Prompt injection defense

- **System prompt:** the rules live in a real `system` message, not in the user message. It states that text inside the tags is quoted data, never instructions, and that the rules must never be revealed.
- **Delimiters:** the question is wrapped in `<question>` and each chunk in `<passage id="n">`. Any `<passage`, `<question`, `<system` or `<instructions` tag inside the text is neutralised, so a document cannot close the delimiter and write its own instructions.
- **Same scan for question and chunks:** a heuristic check looks for phrases such as "ignore previous instructions", role spoofing (`system:`), chat-template tokens and requests to reveal the prompt.
  - A flagged **question** is refused with HTTP 400 and a generic message.
  - A flagged **chunk** is left out of the prompt and logged. The other chunks are still used.
  - The scan runs on every chat request, before retrieval results reach the model. Uploads are not scanned.
- **History:** earlier user messages are escaped the same way.
- **Prompt leak detection:** a random marker (canary) is placed in the system prompt. If it, or a long slice of the rules, appears in an answer, the stream is stopped with a generic error and the event is logged.
- **Limit:** pattern matching catches common wording, not every attack. The delimiters, the leak check and the link filtering are the stronger layers.

### 6.2 Files and downloads

- `GET /files/{id}/download` (Bearer token, owner only) returns `{url, expires_at}`.
- The URL carries `uid`, `exp` and `sig`, where `sig` is HMAC-SHA256 over file id, user id and expiry, keyed with `FILE_URL_SECRET`. It is compared in constant time.
- Lifetime is `FILE_URL_TTL_SECONDS` (300). With `FILE_URL_SINGLE_USE=true` each signature works once (per process).
- `GET /files/{id}/content` accepts either a Bearer token or a valid signature. For a signed request it checks the signature, the expiry and that the file belongs to the signed user. Any failure returns a bare 403.
- Signed downloads are always sent as attachments. Responses carry `X-Content-Type-Options: nosniff` and a restrictive `Content-Security-Policy`.
- The upload folder is never served as static files. Files are stored as `{uuid}{ext}`, and the original name exists only in the database.
- The server refuses to start if `FILE_URL_SECRET` is missing or shorter than 32 characters.

### 6.3 Upload validation

- **Size:** read in 1 MB pieces and stopped at `MAX_UPLOAD_BYTES` (20 MB), HTTP 413.
- **Type by magic bytes:** a PDF must start with `%PDF-`. Text and Markdown must be valid UTF-8 with no NUL bytes. The extension alone is never trusted, and the stored content type comes from the detection, not the client. Mismatch: HTTP 415.
- **Filename:** path parts are removed (`/` and `\`), control characters stripped, length capped at 150, and an empty result becomes `file`.
- **PDFs:**
  - Encrypted PDFs are rejected.
  - More than `MAX_PDF_PAGES` (200) pages is rejected.
  - Embedded JavaScript is rejected (open action, additional actions, the JavaScript name tree, annotation actions).
  - Corrupted PDFs are rejected. Rejections are HTTP 422 with a reason.
- Everything is validated before anything is written to disk.

### 6.4 Output and rendering

- Answers are rendered as Markdown only. Raw HTML is not rendered, and `dangerouslySetInnerHTML` and `rehype-raw` are not used.
- Images and links to hosts outside `ALLOWED_LINK_DOMAINS` are removed, because an injected chunk can use their URLs to leak data. Link text is kept as plain text. With the default empty list, all external links and images are removed.
- The cleanup runs twice: in the backend before an answer is saved (`sanitize_markdown`), and in the frontend at display time (`src/lib/safe-markdown.tsx`).
- Only `http`, `https` and `#` URLs are ever passed to the renderer, so `javascript:` and `data:` links are dropped.
- Links that are kept open with `noopener noreferrer nofollow`.
- The frontend sends a Content-Security-Policy, `X-Content-Type-Options`, `X-Frame-Options` and `Referrer-Policy`. The API sends the last three as well.

### 6.5 Logs and secrets

- Two log files in `LOG_DIR`: `app.log` and `rag_audit.log`. The audit log holds the questions and chunks of each chat request, so it is separate and never exposed by any API route.
- Files rotate daily and keep `LOG_RETENTION_DAYS` (30) days. Rows older than that are purged from the `logs` table once a day.
- A redaction filter removes Bearer tokens, JWTs, `password=`, `token=`, `api_key=` values and passwords inside connection URLs before anything is written.
- Restrict who can read `LOG_DIR`. File mode is 0600 on Linux and macOS. On Windows use folder permissions.
- Secrets stay in environment variables. The startup log no longer prints the database URL or a password hash.

### 6.6 Network

- CORS allows only `CORS_ORIGINS` (default `http://localhost:3000`), with an explicit list of methods and headers. The previous `*` is gone.
- HTTPS redirect is enabled when `ENV=prod`.

## 7. Tests

- `tests/test_security.py` has 12 tests: token signing, tampering, expiry and single use; filename cleaning; magic bytes; encrypted, JavaScript and oversized PDFs; upload size limit; injection scan; delimiter escaping; prompt leak detection; link and image filtering; log redaction.
- They need no database and no Ollama. Run them with `pytest tests`.

## 8. Known limits

- No end-to-end tests for the routes, since they need MySQL and Ollama.
- Single-use download tokens are tracked in memory, so they are not enforced across several workers.
- Log file permissions are not enforced on Windows.
- The injection scan is heuristic.
- Files uploaded before this change keep their old `{id}_{filename}` name on disk until they are deleted or re-uploaded.
