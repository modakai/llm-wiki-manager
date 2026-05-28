# LLM Wiki MVP Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a minimal local FastAPI app that configures an OpenAI-compatible model, uploads documents, generates Markdown LLM Wiki pages, and displays them in a small web UI.

**Architecture:** The MVP uses a local file workspace instead of Supabase or SQLite. FastAPI owns API routing, document parsing, LLM calls, Wiki file writing, and static UI hosting. Wiki content is stored as Markdown under `workspace/wiki`, with raw uploads and parsed text stored beside it for traceability.

**Tech Stack:** Python 3.11+, FastAPI, OpenAI-compatible HTTP calls via `httpx`, PyMuPDF, python-docx, pytest, static HTML/CSS/JS.

---

### Task 1: Core Paths and Config

**Files:**
- Create: `backend/app/core/paths.py`
- Create: `backend/app/core/config.py`
- Test: `backend/tests/test_config_and_paths.py`

- [ ] Write failing tests for workspace directory creation and API key masking.
- [ ] Implement path helpers and local JSON config persistence.
- [ ] Run `pytest backend/tests/test_config_and_paths.py -v`.

### Task 2: Document Parsing

**Files:**
- Create: `backend/app/services/parser_service.py`
- Test: `backend/tests/test_parser_service.py`

- [ ] Write failing tests for `.txt`, `.md`, unsupported `.doc`, and empty text rejection.
- [ ] Implement parsers for `.txt`, `.md`, `.pdf`, `.docx`; reject `.doc` with a LibreOffice note.
- [ ] Run `pytest backend/tests/test_parser_service.py -v`.

### Task 3: Storage and Wiki Generation

**Files:**
- Create: `backend/app/services/storage_service.py`
- Create: `backend/app/services/wiki_service.py`
- Create: `backend/app/prompts/wiki_generation.md`
- Test: `backend/tests/test_storage_and_wiki_service.py`

- [ ] Write failing tests for safe upload storage, parsed text storage, Wiki page writing, index update, and invalid LLM output handling.
- [ ] Implement source IDs, slug generation, Markdown validation, and atomic Wiki writes.
- [ ] Run `pytest backend/tests/test_storage_and_wiki_service.py -v`.

### Task 4: OpenAI-Compatible LLM Client

**Files:**
- Create: `backend/app/services/llm_service.py`
- Test: `backend/tests/test_llm_service.py`

- [ ] Write failing tests using a fake transport for success and auth/network-style errors.
- [ ] Implement a small `httpx` client against `/chat/completions`.
- [ ] Run `pytest backend/tests/test_llm_service.py -v`.

### Task 5: API and Minimal UI

**Files:**
- Create: `backend/app/main.py`
- Create: `backend/app/api/settings.py`
- Create: `backend/app/api/uploads.py`
- Create: `backend/app/api/wiki.py`
- Create: `backend/app/web/index.html`
- Create: `backend/app/web/app.js`
- Create: `backend/app/web/style.css`
- Create: `backend/pyproject.toml`
- Create: `backend/README.md`

- [ ] Wire routes for model settings, upload, Wiki generation, page list, and page content.
- [ ] Build a dense utility UI with model settings, upload, page list, and Markdown preview.
- [ ] Run full pytest suite and start `uvicorn app.main:app --reload`.
