"""Every service-layer error reaches the client as its HTTP status, never as a 500."""

import inspect

from fastapi import APIRouter
from fastapi.testclient import TestClient

from bloom.main import DOMAIN_ERRORS, create_app
from bloom.services import errors


def test_every_service_error_has_a_status():
    # A new error class added to errors.py without a mapping would escape as a 500.
    defined = {
        cls for _, cls in inspect.getmembers(errors, inspect.isclass) if issubclass(cls, Exception) and cls.__module__ == errors.__name__
    }
    assert defined == set(DOMAIN_ERRORS)


def test_errors_map_to_their_status_and_detail():
    app = create_app()
    router = APIRouter(tags=["test"])
    raised = {"with-message": errors.ConflictError("Name taken"), "bare": errors.NotFoundError()}

    @router.get("/raise/{kind}")
    def _raise(kind: str) -> None:
        raise raised[kind]

    app.include_router(router)
    client = TestClient(app)

    assert client.get("/raise/with-message").status_code == 409
    assert client.get("/raise/with-message").json() == {"detail": "Name taken"}
    # An error raised without a message still gets a readable detail.
    assert client.get("/raise/bare").json() == {"detail": "Not found"}
