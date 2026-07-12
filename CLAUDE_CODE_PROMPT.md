# Claude Code — Bootstrap prompt for Bloom

This file contains two prompts. Use them in order:
1. **Planning prompt** — paste first. Claude Code reads the README, asks questions,
   and produces a plan. You review and approve it. No code is written yet.
2. **Execution prompt** — paste after you approve the plan. Claude Code builds it
   phase by phase.

Keep `README.md` in the project root so Claude Code reads it as the source of truth.

---

## PROMPT 1 — PLANNING (paste this first)

You are helping me bootstrap **Bloom**, a self-hosted specialty coffee tracking API.
Before writing any code, read `README.md` in full — it is the source of truth for the
architecture, data model, design decisions, and folder structure. Do not contradict it;
if you think something in it is wrong, raise it explicitly and wait for my decision.

**Your task in this first step is planning only. Do not write application code yet.**

Do the following:

1. Read `README.md` and echo back a concise summary of what you understood: the stack,
   the six entities, the layering rule (routes → services → repositories → db, with
   domain as pure functions), and the user/role model. This confirms we're aligned.

2. Ask me about any genuine ambiguities before planning. Likely open questions:
   - Python version and whether to use `uv` (README says yes).
   - `psycopg` version (3.x) and async vs sync SQLAlchemy — I lean **sync** for
     simplicity unless you make a strong case otherwise.
   - How the first admin is bootstrapped: env vars (`BLOOM_ADMIN_EMAIL` /
     `BLOOM_ADMIN_PASSWORD`) read on startup, or a `bloom create-admin` CLI command.
   - Whether user self-registration is open or admin-only.
   - Token strategy: access token only, or access + refresh.
   Ask these (and any others you spot) as a short numbered list. Wait for my answers.

3. Once answered, produce a **phased implementation plan** as a checklist I can approve.
   Suggested phases, but propose your own if better:
   - **Phase 0 — Scaffolding:** `pyproject.toml` (uv), folder structure exactly as in
     the README, `core/config.py`, `db/base.py` + `db/session.py`, FastAPI app factory
     in `main.py` with a `/health` endpoint, Alembic initialised, docker-compose for
     Postgres. Goal: app boots and connects to the DB.
   - **Phase 1 — Domain layer (pure, test-first):** implement `domain/calculations.py`
     and `domain/constants.py` from the README's specs, with full pytest unit tests.
     No DB, no FastAPI. This is the isolated core; it should have the best test coverage
     in the project.
   - **Phase 2 — Models & first migration:** SQLAlchemy models for all six tables
     matching the README's constraints (CHECKs, FKs, ON DELETE policies, TIMESTAMPTZ,
     NUMERIC, TEXT[] for descriptors). Generate and review the initial Alembic migration.
     Verify `alembic upgrade head` builds the schema on a clean DB.
   - **Phase 3 — Auth & users:** user model, password hashing, JWT, OAuth2 password
     flow, `get_current_user` / `require_admin` dependencies, first-admin bootstrap,
     user CRUD routes (admin-gated where appropriate).
   - **Phase 4 — Core resources:** repositories → services → routes for bean, brew,
     tasting, plus read routes for brew_method and equipment. Enforce ownership
     (users touch their own data; admins see all). Wire the domain calculations into
     brew creation (compute & store extraction_yield when only TDS is given).
   - **Phase 5 — Tests & polish:** API tests against a disposable test DB, seed/fixture
     data, README run-commands verified end to end.

4. For each phase, list the concrete files created/changed and a one-line "done when…"
   acceptance check. Flag anything in the README you'd push back on (for example, the
   pending `user → bean` ON DELETE decision — recommend a default and ask me).

5. Stop after presenting the plan. Wait for my explicit "approved, start Phase 0"
   before writing code.

Constraints throughout:
- All code, comments, identifiers, and commit messages in **English**.
- Respect the layering rule. `domain/` never imports ORM/FastAPI. Routes never run SQL.
- Typed SQLAlchemy 2.x (`Mapped[...]`), Pydantic v2, FastAPI dependency injection.
- Small, reviewable commits, one concern each. Conventional Commit messages.

---

## PROMPT 2 — EXECUTION (paste after you approve the plan)

Great. Proceed with the approved plan, **one phase at a time**. For each phase:

1. State which phase you're starting and the files you'll create or change.
2. Implement it following the README's architecture and the layering rule.
3. Write tests for that phase in the same step (test-first for the domain layer in
   Phase 1). Run them.
4. Run the app or migrations as relevant to prove the phase's "done when…" check passes,
   and show me the output.
5. Summarise what changed, then **stop and wait for my review** before the next phase.
   Do not run ahead into the following phase.

Rules:
- If reality diverges from the plan (a dependency, a constraint, a better approach),
  pause and tell me before deviating — don't silently improvise architecture.
- Never store secrets in code. Use `.env` (git-ignored) and `core/config.py`.
- Keep `domain/` pure. If you catch yourself importing a session into it, stop — the
  logic belongs in a service instead.
- After each phase, remind me of the exact command(s) to verify it myself.

Start with Phase 0.
