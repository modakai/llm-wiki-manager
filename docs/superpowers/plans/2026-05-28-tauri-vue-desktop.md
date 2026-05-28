# Tauri Vue Desktop Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Tauri 2 + Vue 3 desktop shell that reuses the existing FastAPI backend API for the LLM Wiki MVP.

**Architecture:** The desktop app lives under `desktop/`. Vue owns the UI and calls `http://127.0.0.1:8000` during this phase. Tauri provides the desktop window and future sidecar boundary, but Python process management is intentionally deferred to keep this slice verifiable.

**Tech Stack:** Tauri 2, Vue 3, Vite, TypeScript, Vitest, Rust.

---

### Task 1: Desktop Project Skeleton

**Files:**
- Create: `desktop/package.json`
- Create: `desktop/index.html`
- Create: `desktop/tsconfig.json`
- Create: `desktop/vite.config.ts`
- Create: `desktop/src-tauri/*`

- [ ] Create a minimal Vue/Vite/Tauri project.
- [ ] Keep Tauri pointed at Vite dev server port `1420`.

### Task 2: API Client With Tests

**Files:**
- Create: `desktop/src/services/api.ts`
- Create: `desktop/src/types.ts`
- Create: `desktop/src/services/api.test.ts`

- [ ] Write failing tests for settings save, upload, wiki generation, and API error handling.
- [ ] Implement the typed API client.
- [ ] Run `npm test -- --run`.

### Task 3: Vue Workbench UI

**Files:**
- Create: `desktop/src/main.ts`
- Create: `desktop/src/App.vue`
- Create: `desktop/src/style.css`
- Create: `desktop/src/env.d.ts`

- [ ] Implement a three-pane desktop workbench: settings/upload, page list, Markdown preview.
- [ ] Add clear status messages for backend disconnected, parse failures, and model errors.
- [ ] Run `npm run build`.

### Task 4: Verification

**Files:**
- Modify: `desktop/README.md`

- [ ] Document running backend and desktop together.
- [ ] Run backend tests.
- [ ] Run frontend tests.
- [ ] Run frontend build.
- [ ] Run `npm run tauri:info` or equivalent Tauri check with Rust PATH set.
