"""CORS lets the configured frontend call the API, and only with what the UI sends."""

from bloom.core.config import get_settings


def _preflight(client, method="PATCH", headers="authorization,content-type", origin=None):
    return client.options(
        "/brews/1",
        headers={
            "Origin": origin or get_settings().FRONTEND_HOST,
            "Access-Control-Request-Method": method,
            "Access-Control-Request-Headers": headers,
        },
    )


def test_frontend_preflight_is_allowed(client):
    resp = _preflight(client)
    assert resp.status_code == 200
    assert resp.headers["access-control-allow-origin"] == get_settings().FRONTEND_HOST
    # Auth is a bearer header, so cookies are never invited along.
    assert "access-control-allow-credentials" not in resp.headers


def test_unexpected_header_is_refused(client):
    assert _preflight(client, headers="x-anything").status_code == 400


def test_unexpected_method_is_refused(client):
    assert _preflight(client, method="TRACE").status_code == 400


def test_unknown_origin_is_refused(client):
    assert _preflight(client, origin="https://evil.example").status_code == 400
