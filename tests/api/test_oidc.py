"""OIDC single sign-on: account linking, group roles, and forced-SSO mode.

The identity provider is replaced by a fake whose ``authorize_access_token`` returns the
claims under test, so these exercise Bloom's rules, not Authlib's token validation.
"""

from urllib.parse import parse_qs, urlparse

import pytest

from bloom.core.config import get_settings
from bloom.core.security import decode_token
from bloom.repositories import users as users_repo
from bloom.routes import auth as auth_routes


class FakeIdP:
    claims: dict = {}

    async def authorize_redirect(self, request, redirect_uri):
        from fastapi.responses import RedirectResponse

        return RedirectResponse(f"https://idp.example/authorize?redirect_uri={redirect_uri}", status_code=302)

    async def authorize_access_token(self, request):
        return {"userinfo": self.claims}


@pytest.fixture(autouse=True)
def oidc_settings(monkeypatch):
    """Turn OIDC on for every test here (autouse, so it is in place before the app is built)."""
    settings = get_settings()
    for name, value in {
        "OIDC_ISSUER": "https://idp.example",
        "OIDC_CLIENT_ID": "bloom",
        "OIDC_CLIENT_SECRET": "secret",
        "OIDC_REDIRECT_URI": "http://testserver/api/v1/auth/oidc/callback",
    }.items():
        monkeypatch.setattr(settings, name, value)
    return settings


@pytest.fixture
def idp(monkeypatch):
    fake = FakeIdP()
    monkeypatch.setattr(auth_routes, "oidc_client", lambda: fake)
    return fake


def _sso(client, idp, **claims) -> tuple[int | None, str | None]:
    """Run the callback with ``claims``; return (user id from the token, error code)."""
    idp.claims = {"sub": "sub-1", "email": "new@example.com", "email_verified": True} | claims
    resp = client.get("/auth/oidc/callback", follow_redirects=False)
    assert resp.status_code == 302
    location = urlparse(resp.headers["location"])
    assert location.path == "/login"
    if location.fragment.startswith("token="):
        payload = decode_token(location.fragment.removeprefix("token="), expected_type="access")
        return int(payload["sub"]), None
    return None, parse_qs(location.query)["error"][0]


def test_auth_config_reports_methods(client, oidc_settings, monkeypatch):
    assert client.get("/auth/config").json() == {"local_auth_enabled": True, "oidc_enabled": True}
    monkeypatch.setattr(oidc_settings, "DISABLE_LOCAL_AUTH", True)
    assert client.get("/auth/config").json() == {"local_auth_enabled": False, "oidc_enabled": True}


def test_login_redirects_to_idp(client, idp):
    resp = client.get("/auth/oidc/login", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["location"].startswith("https://idp.example/authorize")


def test_endpoints_404_when_oidc_is_off(client, oidc_settings, monkeypatch):
    monkeypatch.setattr(oidc_settings, "OIDC_ISSUER", None)
    assert client.get("/auth/oidc/login").status_code == 404
    assert client.get("/auth/oidc/callback").status_code == 404


def test_first_login_creates_a_linked_user(client, idp, db):
    user_id, error = _sso(client, idp, preferred_username="Newbie")
    assert error is None
    user = users_repo.get_by_id(db, user_id)
    assert (user.email, user.username, user.role, user.oidc_subject) == ("new@example.com", "newbie", "user", "sub-1")
    # The token works against the API.
    token_user = _sso(client, idp)[0]
    assert token_user == user_id


def test_username_clash_gets_a_suffix(client, idp, users, db):
    user_id, _ = _sso(client, idp, preferred_username="alice")
    assert users_repo.get_by_id(db, user_id).username == "alice-2"


def test_existing_user_is_linked_by_email(client, idp, users, db):
    user_id, _ = _sso(client, idp, email="ALICE@example.com")
    assert user_id == users["alice"].id
    db.refresh(users["alice"])
    assert users["alice"].oidc_subject == "sub-1"
    # Later logins match on sub even if the IdP email changes.
    assert _sso(client, idp, email="renamed@example.com")[0] == users["alice"].id


def test_unverified_email_does_not_link(client, idp, users, oidc_settings, monkeypatch):
    # Default: the claim must be true.
    assert _sso(client, idp, email="alice@example.com", email_verified=None) == (None, "oidc_denied")
    assert _sso(client, idp, email="alice@example.com", email_verified=False) == (None, "oidc_denied")
    # Relaxed for IdPs that never send the claim (Entra) — but an explicit false still refuses.
    monkeypatch.setattr(oidc_settings, "OIDC_REQUIRE_EMAIL_VERIFIED", False)
    assert _sso(client, idp, email="alice@example.com", email_verified=False) == (None, "oidc_denied")
    assert _sso(client, idp, email="alice@example.com", email_verified=None)[0] == users["alice"].id


def test_unverified_email_does_not_create(client, idp, oidc_settings, monkeypatch, db):
    # Otherwise someone could claim an unverified address first and lock its owner out.
    assert _sso(client, idp, email_verified=None) == (None, "oidc_denied")
    assert _sso(client, idp, email_verified="false") == (None, "oidc_denied")
    assert users_repo.get_by_email(db, "new@example.com") is None
    # Same relaxation as linking: an absent claim is accepted when the check is off.
    monkeypatch.setattr(oidc_settings, "OIDC_REQUIRE_EMAIL_VERIFIED", False)
    assert _sso(client, idp, email_verified=None)[1] is None


def test_email_already_linked_to_another_sub_is_refused(client, idp, users):
    _sso(client, idp, email="alice@example.com")
    assert _sso(client, idp, sub="someone-else", email="alice@example.com") == (None, "oidc_denied")


def test_inactive_user_is_refused(client, idp, users, db):
    users["alice"].is_active = False
    db.commit()
    assert _sso(client, idp, email="alice@example.com") == (None, "oidc_denied")


def test_auto_create_off_only_admits_existing_users(client, idp, users, oidc_settings, monkeypatch):
    monkeypatch.setattr(oidc_settings, "OIDC_AUTO_CREATE_USERS", False)
    assert _sso(client, idp) == (None, "oidc_denied")
    assert _sso(client, idp, email="bob@example.com")[0] == users["bob"].id


def test_allowed_groups_gate(client, idp, oidc_settings, monkeypatch):
    monkeypatch.setattr(oidc_settings, "OIDC_ALLOWED_GROUPS", "bloom-users, coffee people")
    assert _sso(client, idp, groups=["other"]) == (None, "oidc_denied")
    # Group names may contain spaces.
    assert _sso(client, idp, groups=["coffee people"])[1] is None


def test_admin_groups_promote_and_demote(client, idp, users, db, oidc_settings, monkeypatch):
    monkeypatch.setattr(oidc_settings, "OIDC_ADMIN_GROUPS", "bloom-admin")
    monkeypatch.setattr(oidc_settings, "OIDC_GROUPS_CLAIM", "realm_access.roles")
    alice_id, _ = _sso(client, idp, email="alice@example.com", realm_access={"roles": ["bloom-admin"]})
    # The test session still caches alice from the fixture; reload what the request committed.
    db.expire_all()
    assert users_repo.get_by_id(db, alice_id).role == "admin"
    _sso(client, idp, email="alice@example.com", realm_access={"roles": []})
    db.expire_all()
    assert users_repo.get_by_id(db, alice_id).role == "user"


def test_idp_failure_redirects_with_error(client, idp, monkeypatch):
    async def boom(request):
        raise RuntimeError("state mismatch")

    monkeypatch.setattr(idp, "authorize_access_token", boom)
    resp = client.get("/auth/oidc/callback", follow_redirects=False)
    assert resp.headers["location"] == "/login?error=oidc_failed"


def test_conflict_on_create_redirects_with_error(client, idp, monkeypatch):
    # A concurrent first login won the insert: the browser gets the login page, not a JSON 409.
    from bloom.repositories import users as repo

    monkeypatch.setattr(repo, "add_if_free", lambda db, **kw: None)
    assert _sso(client, idp) == (None, "oidc_failed")


def test_disable_local_auth_blocks_password_endpoints(client, users, oidc_settings, monkeypatch):
    monkeypatch.setattr(oidc_settings, "DISABLE_LOCAL_AUTH", True)
    assert client.post("/auth/token", data={"username": "alice", "password": "alicepass1"}).status_code == 403
    assert client.post("/auth/recover-password", json={"email": "alice@example.com"}).status_code == 403
    assert client.post("/auth/reset-password", json={"token": "x", "new_password": "whatever1"}).status_code == 403


def test_disable_local_auth_skips_invite_email(client, admin_headers, oidc_settings, monkeypatch):
    from bloom.services import email_service

    sent = []
    monkeypatch.setattr(email_service, "send_new_account_email", lambda **kw: sent.append(kw))
    monkeypatch.setattr(oidc_settings, "DISABLE_LOCAL_AUTH", True)
    resp = client.post("/users", headers=admin_headers, json={"email": "carol@example.com", "username": "carol"})
    assert resp.status_code == 201
    assert sent == []
