from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def _assert_error(resp, status: int, code: str) -> None:
    assert resp.status_code == status
    body = resp.json()
    assert set(body) == {"error"}
    assert body["error"]["code"] == code
    assert "message" in body["error"]
    assert "details" in body["error"]


def test_health_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_unknown_route_uniform_404(client):
    _assert_error(client.get("/nope"), 404, "not_found")


def test_wrong_method_uniform_405(client):
    _assert_error(client.put("/health"), 405, "method_not_allowed")


def test_validation_error_names_field(client):
    resp = client.get("/books", params={"limit": 0})
    _assert_error(resp, 422, "validation_error")
    assert resp.json()["error"]["details"][0]["loc"][-1] == "limit"


def test_openapi_has_scheme_error_model_and_routes(client):
    spec = client.get("/openapi.json").json()
    assert "APIKeyHeader" in spec["components"]["securitySchemes"]
    assert "ErrorResponse" in spec["components"]["schemas"]
    for path in (
        "/books",
        "/books/{book_id}",
        "/members",
        "/members/{member_id}",
        "/loans",
        "/loans/overdue",
        "/loans/{loan_id}",
        "/loans/{loan_id}/return",
    ):
        assert path in spec["paths"]
    assert "security" in spec["paths"]["/books"]["post"]
    assert "security" not in spec["paths"]["/books"]["get"]


def test_write_without_key_is_401(client):
    _assert_error(client.post("/books", json={}), 401, "unauthorized")
    _assert_error(client.delete("/members/1", headers={"X-API-Key": "wrong"}), 401, "unauthorized")


def test_write_with_unset_key_is_503(settings):
    app = create_app(Settings(library_api_key=None, database_url=settings.database_url))
    with TestClient(app) as c:
        _assert_error(
            c.delete("/books/1", headers={"X-API-Key": "x"}), 503, "api_key_not_configured"
        )


def test_overdue_not_shadowed_by_loan_id(client):
    # "overdue" must never be parsed as a loan id (would be a 422 on the int path param)
    assert client.get("/loans/overdue").status_code != 422
