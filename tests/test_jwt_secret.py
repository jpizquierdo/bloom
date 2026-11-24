"""Startup refuses a missing, placeholder or short JWT signing key."""

import pytest
from fastapi.testclient import TestClient

from bloom import main
from bloom.core.config import MIN_JWT_SECRET_LENGTH, Settings


def test_placeholder_secret_is_rejected():
    # The shipped default is shorter than the minimum, so an untouched config fails.
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        Settings().require_strong_jwt_secret()


def test_short_secret_is_rejected():
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        Settings(JWT_SECRET="x" * (MIN_JWT_SECRET_LENGTH - 1)).require_strong_jwt_secret()


def test_long_enough_secret_is_accepted():
    Settings(JWT_SECRET="x" * MIN_JWT_SECRET_LENGTH).require_strong_jwt_secret()


def test_app_will_not_start_with_a_weak_secret(monkeypatch):
    # The DB step must never be reached: the check runs first.
    monkeypatch.setattr(main, "get_settings", lambda: Settings(JWT_SECRET="weak"))
    monkeypatch.setattr(main.init_db, "init_db", lambda: pytest.fail("startup continued past the secret check"))
    with pytest.raises(RuntimeError, match="JWT_SECRET"), TestClient(main.create_app()):
        pass


def test_partial_oidc_config_is_rejected():
    with pytest.raises(RuntimeError, match="OIDC_ISSUER"):
        Settings(OIDC_ISSUER="https://idp.example").require_valid_auth_config()


def test_disabling_local_auth_without_oidc_is_rejected():
    # Nobody could log in, so refuse to start.
    with pytest.raises(RuntimeError, match="DISABLE_LOCAL_AUTH"):
        Settings(DISABLE_LOCAL_AUTH=True).require_valid_auth_config()


def test_full_oidc_config_with_local_auth_disabled_is_accepted():
    Settings(
        OIDC_ISSUER="https://idp.example",
        OIDC_CLIENT_ID="bloom",
        OIDC_CLIENT_SECRET="secret",
        OIDC_REDIRECT_URI="https://bloom.example/api/v1/auth/oidc/callback",
        DISABLE_LOCAL_AUTH=True,
    ).require_valid_auth_config()
