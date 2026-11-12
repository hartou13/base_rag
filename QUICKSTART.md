# Base RAG API - Quickstart

## Prerequisites

- **Python 3.12+** and **uv**
- **A MySQL database.** Create an empty database (for example `base_rag`) and put its connection settings in `.env` (`MYSQL_DATABASE`, `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`). Tables are created by the Alembic migrations.
- **A Chroma database.** Chroma runs embedded in the API and stores its data on disk, so there is no server to install. It is created automatically on first use in `data/chroma` (change it with `CHROMA_PATH`). Keep that folder: it holds the vectors for every collection.
- **Ollama.** A local Ollama server with an embedding model (`qwen3-embedding`) for indexing, and an `OLLAMA_API_KEY` in `.env` for answers.

## Install and set up the environment

1. Install uv, a modern Python package manager:

   **macOS and Linux:**

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

   **Windows:**

   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

   ### Project initialisation and virtual environment

   **Windows (PowerShell)**, at the root of the repository (`back-pyxis`):

   ```powershell
   # Only if `pyproject.toml` does not exist yet
   uv init

   uv venv
   # Optional: `uv run` and `uv sync` work without activation
   .\.venv\Scripts\Activate.ps1
   ```

   **macOS and Linux** (equivalent):

   ```bash
   uv init
   uv venv
   source .venv/bin/activate
   ```

2. Use uv to set up your environment:

   ```bash
   # Sync the environment
   uv sync
   ```

3. Generate a migration after changing your models:

   ```bash
   alembic -c alembic.ini revision --autogenerate -m "description of your changes"
   ```

4. Apply the migrations to your database:

   ```bash
   alembic -c alembic.ini upgrade head
   ```

5. Start the application (for now):

   ```bash
   uvicorn main:app --reload
   ```

## Optional settings

- `CHAT_HISTORY_LIMIT` (default `20`): how many past messages of a session are sent to the model on each chat call.

## Security settings

Copy `.env.example` to `.env` and fill it in. `FILE_URL_SECRET` is **required** (generate one with `python -c "import secrets;print(secrets.token_hex(32))"`).

| Variable | Default | Purpose |
| --- | --- | --- |
| `FILE_URL_SECRET` | none, required | Key used to sign download URLs (32+ characters) |
| `FILE_URL_TTL_SECONDS` | `300` | Lifetime of a signed download URL |
| `FILE_URL_SINGLE_USE` | `false` | A signed URL works only once (per process) |
| `MAX_UPLOAD_BYTES` | `20971520` | Largest accepted upload (20 MB) |
| `MAX_PDF_PAGES` | `200` | Largest accepted PDF |
| `ALLOWED_LINK_DOMAINS` | empty | Comma-separated hosts allowed in answer links and images; empty removes all |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated origins allowed to call the API from a browser |
| `LOG_DIR` | `data/logs` | Where `app.log` and `rag_audit.log` are written |
| `LOG_RETENTION_DAYS` | `30` | How long log files and `logs` table rows are kept |

On the frontend, set `NEXT_PUBLIC_ALLOWED_LINK_DOMAINS` to the same list as `ALLOWED_LINK_DOMAINS`.

## Adding a module

```bash
python command/module_create.py <module_name>
```

This creates `src/<module_name>/` with empty `routers`, `services`, `models` and `dto` packages. Then:

1. Write the router, service, model and DTO files. A router calls one service function per URL, and the logic lives in the service file (names end in `_service`). Use uuid strings as primary keys.
2. Register the router in `main.py` with `app.include_router(...)`.
3. Import any new model in `alembic/env.py`, then generate and apply a migration (steps 3 and 4 above).
