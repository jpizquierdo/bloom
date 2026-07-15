# Bloom — web UI

A React SPA for the Bloom API. The API client is **generated from the backend's OpenAPI
schema**, so the two never drift: change a route or a schema, regenerate, and TypeScript
tells you what broke.

## Stack

| | |
|---|---|
| Build | Vite + React 19 + TypeScript |
| Styling | Tailwind v4 + [shadcn/ui](https://ui.shadcn.com) (components are vendored in `src/components/ui` — edit them freely) |
| Routing | TanStack Router (file-based, type-safe) |
| Server state | TanStack Query |
| API client | `@hey-api/openapi-ts` → `src/client` (generated, do not edit) |
| Forms | react-hook-form + zod |

## Run it

```bash
npm install
npm run dev     # http://localhost:5173, proxying /api to http://localhost:8000
```

The API must be running, and must allow this origin — that is what `FRONTEND_HOST` does in the
backend's `.env`. Point the proxy at an API on another port with `BLOOM_API_URL=… npm run dev`.

Log in with the bootstrapped admin (`BLOOM_ADMIN_EMAIL` / `BLOOM_ADMIN_PASSWORD`); there is no
public sign-up.

## How it ships

There is **no separate frontend image**. `docker build` at the repo root compiles this app in a
Node stage and copies `dist/` into the Python image, where FastAPI serves it from the API's own
origin. That is why the client's base URL is empty (`src/lib/api-config.ts`) and every request
goes to a relative `/api/v1/…`: one image works at any hostname, behind any reverse proxy, with
no rebuild. Set `VITE_API_URL` only if you want a build that targets an API somewhere else.

## Regenerate the API client

After any change to the backend's routes or schemas:

```bash
cd .. && uv run python scripts/dump_openapi.py   # refresh openapi.json
cd frontend && npm run generate-client           # rewrite src/client
npm run typecheck
```

## Layout

```
src/
  client/         generated API client + TanStack Query hooks (never hand-edited)
  components/
    ui/           shadcn primitives — yours to modify
    data/         DataTable, ResourceDialog, DeleteAlert, RowActions… the CRUD kit
    layout/       sidebar, user menu, theme toggle
    brews/        brew + tasting dialogs, extraction diagnostics
  lib/            api client config, auth, formatting, domain constants
  routes/         file-based routes; everything under `_app` requires a login
```

## Adding a resource

The CRUD pieces are shared, so a new resource is one file in `src/routes/_app/`. Copy
`roasters/index.tsx` — the smallest complete example — and supply three things: the column
definitions, a zod form schema, and the generated query/mutation hooks. `DataTable`,
`ResourceDialog` and `DeleteAlert` handle the rest.

For a **detail page**, add a `$id.tsx` route beside `index.tsx` and make the list rows
navigate to it (`onRowClick`); `roasters/$roasterId.tsx`, `beans/$beanId.tsx` and
`brews/$brewId.tsx` are the examples. For a **long pick-list** (e.g. beans), use the
searchable `Combobox` (`components/data/combobox.tsx`) instead of a plain `Select`.

Two API rules every page must respect:

- **Ownership.** Anyone reads everything; only the row's creator (or an admin) may edit or
  delete it. Use `canEdit(row, user)` from `lib/auth.ts` to drive `RowActions`.
- **No nulls on PATCH.** The API rejects an explicit `null` for fields backed by NOT NULL
  columns. Build payloads with `stripEmpty()` from `lib/format.ts`, which omits empty keys
  instead of sending `null`.

## Not implemented yet

`/signup` and `/recover-password` render the full form, but the submit button is disabled:
the API has no sign-up or password-reset endpoint. When those land, swap the disabled button
for the generated mutation — nothing else changes.
