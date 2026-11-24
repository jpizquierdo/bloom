# Single sign-on (OIDC)

Bloom can log people in through any OpenID Connect provider (Keycloak, Authentik, Entra ID,
Google, Okta…), alongside passwords or instead of them. It uses the Authorization Code flow with
PKCE and verifies the ID token against the provider's signing keys. SSO is off until you
configure it.

## Configuration

Register a **confidential** client with the provider, with this redirect URI:

```
https://<your-host>/api/v1/auth/oidc/callback
```

Then set:

| Variable | Default | Purpose |
|----------|---------|---------|
| `OIDC_ISSUER` | — | Issuer URL. Discovery reads `<issuer>/.well-known/openid-configuration`. |
| `OIDC_CLIENT_ID` / `OIDC_CLIENT_SECRET` | — | The client's credentials. |
| `OIDC_REDIRECT_URI` | — | The callback above, exactly as registered with the provider. |
| `OIDC_SCOPES` | `openid profile email` | Add `groups` (or your provider's equivalent) for group mapping. |
| `OIDC_AUTO_CREATE_USERS` | `true` | Create an account on first SSO login. With `false`, only existing accounts get in. |
| `OIDC_GROUPS_CLAIM` | `groups` | ID-token claim with the groups. Use dot notation for nested claims (`realm_access.roles`). |
| `OIDC_ADMIN_GROUPS` | empty | Comma-separated groups that grant admin. When set, the role is synced on **every** login: members are promoted, everyone else is demoted. |
| `OIDC_ALLOWED_GROUPS` | empty | Comma-separated groups allowed in. Empty lets everyone in. Admins always pass. |
| `OIDC_REQUIRE_EMAIL_VERIFIED` | `true` | Linking or creating an account by email requires `email_verified=true`. Set it to `false` for providers that never send the claim (Entra ID). An explicit `false` is still refused. |
| `DISABLE_LOCAL_AUTH` | `false` | Turn off passwords. The login page redirects straight to the provider, and the password login, recovery and reset endpoints answer `403`. |

SSO is on once the first four are set. The app refuses to start if only some of them are set, or
if `DISABLE_LOCAL_AUTH=true` is set without SSO, since nobody could log in.

Group names may contain spaces; only the commas separate them.

## How accounts are matched

On each SSO login Bloom looks for the account:

1. By the provider's `sub` claim, for accounts that have already used SSO.
2. Otherwise by email, for accounts not linked yet. This is how existing users keep their beans,
   brews and tastings. The email must be verified (see `OIDC_REQUIRE_EMAIL_VERIFIED`); otherwise
   anyone who can set an arbitrary email at the provider could take over that account.
3. Otherwise a new account is created (`role=user`, or `admin` through `OIDC_ADMIN_GROUPS`), with
   the same email rule — so nobody can claim an unverified address before its owner — if
   `OIDC_AUTO_CREATE_USERS` is on. Its username comes from `preferred_username`, or from the
   email before the `@`, with a `-2`, `-3`… suffix if it is taken.

Once matched, the account stays linked to that `sub`, even if the email changes at the provider.
The login is refused when the account is deactivated (SSO never reactivates it), or when the
email belongs to an account already linked to a different `sub`.

The first admin still comes from `BLOOM_ADMIN_EMAIL`. If that admin later signs in through SSO
with the same verified email, the two are linked.

## Roles and groups

- **Neither group variable set:** everyone at the provider can log in, and roles are managed in
  Bloom's **Users** page as usual.
- **`OIDC_ALLOWED_GROUPS` set:** only members of those groups (or admins) can log in.
- **`OIDC_ADMIN_GROUPS` set:** the provider decides who is admin, at every login. A role you
  change by hand in Bloom is overwritten on that user's next login.

Groups are read from the **ID token**, not the userinfo endpoint. Many providers leave them out
of the ID token by default, so you may need to add a mapper (see the provider notes below).

Group changes take effect at the next login. A session lasts `ACCESS_TOKEN_EXPIRE_HOURS`
(12 by default).

## Before you disable passwords

- Sign in with SSO at least once with `DISABLE_LOCAL_AUTH=false` and check you get the role you
  expect.
- If you set `OIDC_ADMIN_GROUPS`, make sure your own account is in one of those groups, or your
  next login demotes you.
- With passwords off, users that an admin creates in Bloom get no invite email. They are linked
  by email on their first SSO login.

If the provider fails afterwards, set `DISABLE_LOCAL_AUTH=false` and restart to get password
login back.

## Provider notes

| Provider | Settings |
|----------|----------|
| Keycloak | `OIDC_ISSUER=https://kc.example.com/realms/<realm>`, `OIDC_GROUPS_CLAIM=realm_access.roles` (realm roles) or `groups` (a group-membership mapper). |
| Authentik | `OIDC_ISSUER=https://auth.example.com/application/o/<slug>/`, `OIDC_SCOPES=openid profile email groups`. |
| Entra ID | `OIDC_ISSUER=https://login.microsoftonline.com/<tenant-id>/v2.0`, `OIDC_REQUIRE_EMAIL_VERIFIED=false`. Groups arrive as object IDs, so list IDs in the group variables. |
| Google | `OIDC_ISSUER=https://accounts.google.com`. Google sends no groups, so leave the group variables empty. |
| Pocket ID | `OIDC_ISSUER=https://id.example.com` (its `APP_URL`), `OIDC_SCOPES=openid profile email groups`. See the guide below. |

### Keycloak step by step

1. In your realm, go to **Clients → Create client**. Choose **OpenID Connect** and set
   **Client ID** to `bloom`.
2. Turn **Client authentication** on (confidential client) and keep **Standard flow** enabled.
3. Set **Valid redirect URIs** to `https://<your-host>/api/v1/auth/oidc/callback`.
4. Copy the secret from the client's **Credentials** tab into `OIDC_CLIENT_SECRET`.
5. For admin by role: create a realm role (for example `bloom-admin`) and assign it to your
   admins. Then, in **Clients → bloom → Client scopes → bloom-dedicated**, add a mapper **By
   configuration → User Realm Role** with **Token Claim Name** `realm_access.roles`,
   **Multivalued** on and **Add to ID token** on.
6. Configure Bloom:

   ```env
   OIDC_ISSUER=https://kc.example.com/realms/<realm>
   OIDC_CLIENT_ID=bloom
   OIDC_CLIENT_SECRET=<secret>
   OIDC_REDIRECT_URI=https://<your-host>/api/v1/auth/oidc/callback
   OIDC_GROUPS_CLAIM=realm_access.roles
   OIDC_ADMIN_GROUPS=bloom-admin
   ```

7. Users need an email in Keycloak with **Email verified** on, or they cannot be linked to
   existing Bloom accounts.

### Pocket ID step by step

[Pocket ID](https://pocket-id.org) is a self-hosted, passkey-only provider. Its issuer is its own
`APP_URL`, and it puts the `groups` claim (group **names**) in the ID token when the `groups`
scope is requested.

1. In Pocket ID, go to **Administration → OIDC Clients → Add OIDC Client**. Give it a name
   (`Bloom`), keep it **confidential** (not a public client), and set the callback URL to
   `https://<your-host>/api/v1/auth/oidc/callback`.
2. Click **Create** and copy the client ID and secret. The secret is shown **only once**; if you
   lose it, add a new one under the client's **Credentials** tab.
3. In the client's **Access** tab, under **Allowed User Groups**, tick the groups that may use
   Bloom, or choose **All Users**. A client created in the admin UI starts with no group ticked,
   so nobody can sign in until you choose.
4. For admin by group: create a group under **Administration → User Groups** (for example
   `bloom-admins`) and add your admins. Use the group's **name**, not its friendly name.
5. Configure Bloom:

   ```env
   OIDC_ISSUER=https://id.example.com
   OIDC_CLIENT_ID=<client id>
   OIDC_CLIENT_SECRET=<secret>
   OIDC_REDIRECT_URI=https://<your-host>/api/v1/auth/oidc/callback
   OIDC_SCOPES=openid profile email groups
   OIDC_ADMIN_GROUPS=bloom-admins
   ```

Pocket ID's **Allowed User Groups** already decides who can sign in, so you can leave
`OIDC_ALLOWED_GROUPS` empty. A user outside those groups is stopped by Pocket ID itself and never
reaches Bloom. Bloom must reach `OIDC_ISSUER` from its own container: the token exchange is
server to server.

Pocket ID sends `email_verified` with the email. If linking or creating Bloom accounts fails with
`unverified email` in the log, set `OIDC_REQUIRE_EMAIL_VERIFIED=false` — but only if your users
cannot change their own email in Pocket ID; otherwise one could claim another's Bloom account.

## Troubleshooting

A failed SSO login returns to the login page with one of two messages. The server log says
which case it is.

**"Single sign-on failed"** (`/login?error=oidc_failed`, log: `OIDC callback failed` and a
traceback). The exchange with the provider failed:

- **`redirect_uri_mismatch` or a provider error page:** `OIDC_REDIRECT_URI` must match the
  registered URI exactly, including scheme, host, port and path.
- **Discovery errors:** check that `curl <OIDC_ISSUER>/.well-known/openid-configuration` works
  from the Bloom container.
- **Invalid token or `iat`/`exp` errors:** check the client secret, and that the server's clock
  is in sync (NTP).
- **State mismatch:** the login started on one host name and came back on another (for example
  `localhost` vs. `127.0.0.1`). Use the host from `OIDC_REDIRECT_URI` consistently. Behind HTTPS
  the session cookie is `Secure`, so the site must really be served over HTTPS.

**"Your SSO account is not allowed to use Bloom"** (`/login?error=oidc_denied`, log:
`OIDC login refused: …`). Bloom refused the identity:

| Log reason | Fix |
|------------|-----|
| `subject not in OIDC_ALLOWED_GROUPS` | Add the user to an allowed group, or check that groups reach the ID token and that `OIDC_GROUPS_CLAIM` points at them. |
| `unverified email for …` | Mark the email verified at the provider, or set `OIDC_REQUIRE_EMAIL_VERIFIED=false` if it never sends the claim. |
| `user … is linked to another identity` | That Bloom account is already linked to a different provider user. |
| `inactive user …` | Reactivate the account in Bloom's **Users** page. |
| `no account and OIDC_AUTO_CREATE_USERS is off` | Create the account in Bloom first, with the same email. |
| `no email claim for a new account` | Request the `email` scope and give the user an email at the provider. |
| `no sub claim` | The provider is not returning a standard ID token; check the client's protocol is OpenID Connect. |

To see the claims your provider actually sends, decode an ID token at the provider's own tools
(for example Keycloak's **Client scopes → Evaluate → Generated ID token**).
