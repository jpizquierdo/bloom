# CLAUDE.md

Guidance for AI assistants working in this repository.

## Commit conventions

- Use **Conventional Commit** messages (`feat:`, `fix:`, `chore:`, `docs:`, `test:`…).
- Keep commits small and reviewable — one concern each.
- Write everything in **English**.
- **Do NOT add any Claude/AI attribution to commits.** Specifically:
  - No `Claude-Session:` trailer or any Claude Code session URL.
  - No `Co-Authored-By: Claude` or similar co-authorship / "in collaboration with
    Claude" lines.
  - Commits should read as authored solely by the repository owner.

## Code style

- **Keep comments minimal.** Comment only what the code cannot say itself — the *why*
  behind a non-obvious choice, not the *what*. Do not restate what the line plainly does.
- No header/banner comments describing a file's purpose (a module docstring is enough),
  and no step-numbering narration (`# 1)`, `# 2)`). Match the surrounding file's density.
- **Tests are an exception**: verbose, explanatory comments (expected values, intent of
  each case) are welcome there. This rule targets production code.
- **Public API docs are an exception**: every FastAPI route handler should have a concise
  docstring — FastAPI surfaces it as the endpoint's description in the OpenAPI/Swagger docs.
  Keep it short: what it does plus the access rule (shared / owner / admin). Likewise use
  `Field(description=...)` / `summary=` where it improves the generated docs. Do **not**
  strip these to be terse.

## Secrets

- **NEVER read the `.env` file, under any circumstances.** Do not open it, `cat` it,
  grep it, or print its contents — it holds real production secrets. Use `.env.example`
  when you need to know which variables exist.
- Never write secret values into the repository, commits, logs, or chat output.

## Project conventions

- All code, comments, and identifiers in **English**.
- Respect the layering rule: `routes → services → repositories → db`, with `domain/`
  as pure functions. `domain/` never imports ORM/FastAPI/session; routes contain no
  SQL; repositories are the only DB-access layer.
- Typed SQLAlchemy 2.x (`Mapped[...]`), Pydantic v2, FastAPI dependency injection.
- Every API route is served under `/api/v1` (`settings.API_V1_STR`). **`/health` stays at
  the root** — container healthchecks probe it.
- See `docs/ARCHITECTURE.md` for the architecture, data model, and design decisions
  (source of truth). `README.md` covers how to run and use the project.

## Web UI (`frontend/`)

React + TypeScript SPA: Vite, Tailwind v4, shadcn/ui, TanStack Router + Query,
react-hook-form + zod. See `frontend/README.md` for the stack and how to add a page.

- **`frontend/src/client/` is generated — never edit it by hand.** It is committed, so it
  looks editable, but any change is lost on the next run. After touching a route or a schema:
  `uv run python scripts/dump_openapi.py && (cd frontend && npm run generate-client)`.
- **Ownership**: rows are readable by everyone, editable only by their creator or an admin.
  Drive the UI from `canEdit(row, user)` (`src/lib/auth.ts`) — never re-derive the rule.
- **PATCH never sends `null`**: the API rejects an explicit `null` for fields backed by NOT
  NULL columns (`bloom/schemas/common.py:reject_null`). Build payloads with `stripEmpty()`
  (`src/lib/format.ts`), which omits empty keys.
- Numeric columns arrive as **strings** (`"18.50"`) — format via `src/lib/format.ts`.
- The UI is **served by the API from `bloom/static`**, built into the same image; there is no
  separate frontend container. It therefore calls the API with **relative** URLs — do not
  reintroduce an absolute base URL, or the image stops working behind a reverse proxy.
- Checks: `npm run lint`, `npm run build` (both run in CI, and the build gates the release
  image). Node comes from `nvm`.

## Releasing

The version lives in five places and they must agree: `pyproject.toml`, `uv.lock`, the image
tag in `docker/docker-compose.yml`, `openapi.json`, and `frontend/package.json`. Bump
`pyproject.toml`, then run `uv lock` and `uv run python scripts/dump_openapi.py` to refresh
the derived ones — a stale `uv.lock` fails the Docker build, which runs `uv sync --frozen`.
