from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Loan


def _mk(client: TestClient, h: dict, name: str = "Anna", email: str = "a@x.org", **kw):
    return client.post("/members", json={"name": name, "email": email, **kw}, headers=h)


def test_create_lowercase_default_since_and_duplicate(client, api_headers):
    r = _mk(client, api_headers, email="Anna@Example.org")
    assert r.status_code == 201
    b = r.json()
    assert b["email"] == "anna@example.org"
    assert b["member_since"] == "2025-01-15"
    assert b["open_loans"] == 0
    d = _mk(client, api_headers, email="ANNA@example.org")
    assert d.status_code == 409
    assert d.json()["error"]["code"] == "duplicate_email"


def test_future_date_422(client, api_headers):
    r = _mk(client, api_headers, member_since="2999-01-01")
    assert r.status_code == 422
    assert r.json()["error"]["details"][0]["loc"][-1] == "member_since"


def test_pagination_order(client, api_headers):
    for n in ["Cy", "Al", "Bo"]:
        _mk(client, api_headers, name=n, email=f"{n}@x.org")
    r = client.get("/members?limit=2&offset=1").json()
    assert r["total"] == 3
    assert [i["name"] for i in r["items"]] == ["Bo", "Cy"]
    assert client.get("/members?limit=0").status_code == 422


def test_get_put_patch_delete_404(client, api_headers):
    mid = _mk(client, api_headers).json()["id"]
    assert client.get(f"/members/{mid}").json()["name"] == "Anna"
    r = client.put(f"/members/{mid}", json={"name": "B", "email": "B@x.org"}, headers=api_headers)
    assert r.status_code == 200 and r.json()["email"] == "b@x.org"
    r = client.patch(f"/members/{mid}", json={"name": "C"}, headers=api_headers)
    assert r.json()["name"] == "C" and r.json()["email"] == "b@x.org"
    other = _mk(client, api_headers, email="o@x.org").json()["id"]
    r = client.patch(f"/members/{other}", json={"email": "B@X.org"}, headers=api_headers)
    assert r.status_code == 409
    assert client.delete(f"/members/{mid}", headers=api_headers).status_code == 204
    for resp in (
        client.get(f"/members/{mid}"),
        client.put(f"/members/{mid}", json={"name": "x", "email": "x@x.org"}, headers=api_headers),
        client.patch(f"/members/{mid}", json={}, headers=api_headers),
        client.delete(f"/members/{mid}", headers=api_headers),
    ):
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "not_found"


def test_has_open_loans(client, api_headers, session: Session):
    mid = _mk(client, api_headers).json()["id"]
    now = datetime(2025, 1, 15, tzinfo=UTC)
    session.add(Loan(book_id=1, member_id=mid, loaned_at=now, due_at=now))
    session.commit()
    assert client.get(f"/members/{mid}").json()["open_loans"] == 1
    r = client.delete(f"/members/{mid}", headers=api_headers)
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "has_open_loans"


def test_unauthorized_changes_nothing(client, api_headers):
    mid = _mk(client, api_headers).json()["id"]
    for h in ({}, {"X-API-Key": "wrong"}):
        body = {"name": "Z", "email": "z@x.org"}
        for r in (
            client.post("/members", json=body, headers=h),
            client.put(f"/members/{mid}", json=body, headers=h),
            client.patch(f"/members/{mid}", json=body, headers=h),
            client.delete(f"/members/{mid}", headers=h),
        ):
            assert r.status_code == 401
            assert r.json()["error"]["code"] == "unauthorized"
    assert client.get("/members").json()["total"] == 1
    assert client.get(f"/members/{mid}").json()["name"] == "Anna"
