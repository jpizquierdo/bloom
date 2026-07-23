# Bloom — iOS Shortcut (Apple Shortcuts) guide

Build a menu-driven client for the Bloom API on your iPhone/iPad, runnable by tapping or
by asking Siri ("Hey Siri, Bloom"). It logs in, lets you pick **Bean / Brew / Tasting**,
then **Create / List / Update / Delete**, prompting for the fields and calling the API.

Everything here uses the [Shortcuts app](https://support.apple.com/guide/shortcuts/welcome/ios)
— no coding, just chaining actions.

---

## Before you start

- **Bloom must be reachable over HTTPS** from your phone (e.g. behind a reverse proxy with
  a valid TLS certificate). You're sending a password, so plain HTTP is a bad idea, and a
  self-signed cert won't be trusted by iOS.
- You need a **Bloom account** (email + password). An admin creates it via `POST /users`.
- Know your **base URL**, e.g. `https://bloom.example.com`.

### A note on credentials (important before publishing)

For your **own** use you can store the password in the shortcut. But since you plan to
**share** it, keep the three config values in plain **Text** actions at the very top so
others just edit them — or set the password field to **"Ask Each Time"** so it's never
baked into the shared shortcut. Never publish a shortcut with your real password inside.

---

## Config (top of the shortcut)

Add three **Text** actions and rename their variables (long-press → Rename):

| Variable   | Value (example)              |
|------------|------------------------------|
| `BASE_URL` | `https://bloom.example.com`  |
| `EMAIL`    | `you@example.com`            |
| `PASSWORD` | your password (or use *Ask Each Time*) |

---

## Step 1 — Log in and get a token

The API uses the OAuth2 password flow: `POST /auth/token` with a **form** body returns
`{ "access_token": "...", "token_type": "bearer" }`.

1. **Get Contents of URL**
   - URL: `BASE_URL` + `/auth/token`  (tip: use a **Text** action `"[BASE_URL]/auth/token"`)
   - Method: **POST**
   - Request Body: **Form**
     - `username` → `EMAIL`  *(the API uses email as the username)*
     - `password` → `PASSWORD`
2. **Get Dictionary Value** → key `access_token` from the previous result. Rename this
   variable to `TOKEN`.
3. *(Recommended)* **If** `TOKEN` **has no value** → **Show Alert** "Login failed" → **Stop
   Shortcut**.

You'll reuse `TOKEN` in every authenticated call as the header
`Authorization: Bearer [TOKEN]`.

> Tip: put steps 1–2 in their **own shortcut** ("Bloom Login") that outputs the token, and
> call it with **Run Shortcut** from the main one. Keeps things tidy.

---

## Step 2 — Choose resource and action

1. **Choose from Menu** → prompt "What?" with items: **Bean**, **Brew**, **Tasting**.
2. Inside each, another **Choose from Menu** → "Action": **Create**, **List**, **Update**,
   **Delete**.

Each leaf runs one **Get Contents of URL** with:
- the right **Method** and **URL** (see the reference table below),
- header `Authorization` = `Bearer [TOKEN]`,
- for Create/Update, Request Body: **JSON** built from your inputs.

Finish any branch with **Show Result** / **Quick Look** on the response so you see what the
API returned (or the error detail).

---

## Endpoint reference

All paths are relative to `BASE_URL`. Authenticated calls need the
`Authorization: Bearer [TOKEN]` header.

| Resource | Action | Method & path | Body (JSON) |
|----------|--------|---------------|-------------|
| Bean  | Create | `POST /beans` | `name`*, `roaster`* (a name — created if new), optional: `origin_country`, `region`, `producer`, `variety`, `process`, `roast_level`, `roast_date`, `purchase_date`, `weight_grams`, `price`, `altitude_masl`, `tasting_notes_label`, `notes`, `is_finished` |
| Bean  | List   | `GET /beans` (`?mine=true` for yours) | — |
| Bean  | Update | `PATCH /beans/{id}` | any of the create fields |
| Bean  | Delete | `DELETE /beans/{id}` | — |
| Brew  | Create | `POST /brews` | `bean_id`*, `method_id`*, `dose_grams`*, optional: `grinder_id`, `brewed_at`, `yield_grams`, `water_grams`, `grind_setting`, `water_temp_celsius`, `brew_time_seconds`, `tds_percent`, `extraction_yield_percent`, `notes` |
| Brew  | List   | `GET /brews` (`?mine=true`) | — |
| Brew  | Update | `PATCH /brews/{id}` | any brew field (except `bean_id`/`method_id`) |
| Brew  | Delete | `DELETE /brews/{id}` | — |
| Tasting | Create | `POST /brews/{brew_id}/tastings` | scores 1–10: `aroma`, `acidity`, `sweetness`, `body`, `bitterness`, `aftertaste`, `overall`; `descriptors` (list of strings); `notes`; `tasted_at` |
| Tasting | List (of a brew) | `GET /brews/{brew_id}/tastings` | — |
| Tasting | List (yours) | `GET /tastings?mine=true` | — |
| Tasting | Update | `PATCH /tastings/{id}` | any tasting field |
| Tasting | Delete | `DELETE /tastings/{id}` | — |
| Lookups | List methods / equipment | `GET /brew-methods`, `GET /equipment` | — |
| Roaster | List | `GET /roasters` | — (handy for a picker; you never need to create one by hand) |

\* required. Numbers may be sent as strings (`"15"`) or numbers; the API accepts both.
Dates are ISO (`2026-07-01`), timestamps ISO-8601 (`2026-07-12T08:00:00Z`).

---

## Worked example A — Create a Bean

1. **Ask for Input** (Text) "Bean name?" → variable `name`.
2. **Ask for Input** (Text) "Roaster?" → variable `roaster`. Type it freely: the API reuses the
   roaster if it already knows the name (any capitalisation) and creates it otherwise.
3. *(optional)* **Ask for Input** (Number) "Weight (g)?" → `weight`.
4. **Dictionary** action, add keys:
   - `name` → `name`
   - `roaster` → `roaster`
   - `weight_grams` → `weight` *(skip if you didn't ask)*
5. **Get Contents of URL**
   - URL: `[BASE_URL]/beans`
   - Method: **POST**
   - Headers: `Authorization` = `Bearer [TOKEN]`
   - Request Body: **JSON** → set it to the **Dictionary** from step 4
6. **Show Result** of the response (you'll get the created bean with its `id`).

---

## Worked example B — Create a Brew (with pickers)

A brew needs a `bean_id` and a `method_id`, so first let the user pick them from the API.

1. **Get Contents of URL**: `GET [BASE_URL]/beans`, header `Authorization: Bearer [TOKEN]`.
2. **Choose from List** on that result → the user picks a bean. Then **Get Dictionary
   Value** `id` from the chosen item → `bean_id`.
   - *Nicer labels:* **Repeat with Each** over the beans, build a text
     `"[name] — [roaster.name] (#[id])"` (a bean's `roaster` is a nested object, so take
     **Get Dictionary Value** `name` from it), **Choose from List** of those, then extract the id.
3. **Get Contents of URL**: `GET [BASE_URL]/brew-methods` → **Choose from List** →
   **Get Dictionary Value** `id` → `method_id`.
4. **Ask for Input** (Number) "Dose (g)?" → `dose`.
5. **Dictionary**: `bean_id` → `bean_id`, `method_id` → `method_id`, `dose_grams` → `dose`
   (+ any of `water_grams`, `yield_grams`, `tds_percent`, `grind_setting`, `notes`…).
6. **Get Contents of URL**: `POST [BASE_URL]/brews`, Authorization header, Request Body:
   **JSON** = the dictionary.
7. **Show Result** — the response includes the computed `ratio` and `diagnostics`, and the
   stored `extraction_yield_percent` if you sent `tds_percent` + `yield_grams`.

**Create a Tasting** is the same pattern: `GET /brews` (or `?mine=true`) → pick a brew →
its `id` → ask for the 1–10 scores → `POST /brews/{brew_id}/tastings`.

---

## Delete / Update (any resource)

1. **Get Contents of URL**: `GET` the list (e.g. `/beans`, `/brews`, `/tastings?mine=true`).
2. **Choose from List** → **Get Dictionary Value** `id` → `id`.
3. **Delete:** **Get Contents of URL** `DELETE [BASE_URL]/beans/[id]` with the Authorization
   header. A `204` (empty) response means success.
4. **Update:** ask for the fields to change, build a **Dictionary** with only those, then
   `PATCH [BASE_URL]/beans/[id]` with Request Body **JSON**.

---

## Errors and status codes

The API returns JSON errors like `{ "detail": "..." }`. Handy checks:

- `401` — bad login or missing/expired token → re-run login.
- `403` — you're not the owner/author (or not admin for lookup writes).
- `404` — not found (or someone else's private brew/tasting).
- `422` — validation error; the `detail` lists which field is wrong.

Add an **If** on `access_token`/status where it helps, and always **Show Result** so you can
read `detail`.

---

## Nice-to-haves

- **Siri phrase:** name the shortcut "Bloom" so "Hey Siri, Bloom" runs it. Add it to the
  Home Screen for one-tap access.
- **Speed:** cache the token in a variable within a single run; a token lasts
  `ACCESS_TOKEN_EXPIRE_HOURS` (generous by default), so a re-login is rarely needed.
- **Explore the API first:** open `BASE_URL/docs` (Swagger) in Safari to see every endpoint,
  field, and example response before wiring the shortcut.

---

## Publishing

When it's polished:

1. Remove your real `BASE_URL` / `EMAIL` / `PASSWORD` (leave placeholders, or set `PASSWORD`
   to *Ask Each Time*).
2. Shortcuts → your shortcut → Share → **Copy iCloud Link**.
3. Share the link. Recipients edit the three config Text actions with their own instance and
   credentials.
