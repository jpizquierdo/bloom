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

## Project conventions

- All code, comments, and identifiers in **English**.
- Respect the layering rule: `routes → services → repositories → db`, with `domain/`
  as pure functions. `domain/` never imports ORM/FastAPI/session; routes contain no
  SQL; repositories are the only DB-access layer.
- Typed SQLAlchemy 2.x (`Mapped[...]`), Pydantic v2, FastAPI dependency injection.
- See `docs/ARCHITECTURE.md` for the architecture, data model, and design decisions
  (source of truth). `README.md` covers how to run and use the project.
