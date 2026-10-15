from datetime import UTC, datetime

import pytest
from sqlalchemy.orm import Session

from app.models import Loan, Member

ISBN13 = "978-0-306-40615-7"
ISBN13_PLAIN = "9780306406157"
ISBN10 = "0-8044-2957-X"


def body(**kw):
    d = {
        "title": "The Hobbit",
        "author": "J.R.R. Tolkien",
        "isbn": ISBN13,
        "published_year": 1937,
        "copies": 3,
    }
    d.update(kw)
    return d


def make(client, headers, **kw):
    r = client.post("/books", json=body(**kw), headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


def add_loan(session: Session, book_id: int, returned: bool = False) -> None:
    now = datetime(2025, 1, 1, tzinfo=UTC)
    m = Member(name="M", email=f"m{book_id}{returned}@x.org", member_since=now.date())
    session.add(m)
    session.flush()
    session.add(
        Loan(
            book_id=book_id,
            member_id=m.id,
            loaned_at=now,
            due_at=now,
            returned_at=now if returned else None,
        )
    )
    session.commit()


def test_create_and_get(client, api_headers):
    b = make(client, api_headers)
    assert b["isbn"] == ISBN13_PLAIN
    assert b["available_copies"] == b["copies"] == 3
    assert client.get(f"/books/{b['id']}").json() == b


def test_isbn10_x_lowercase(client, api_headers):
    b = make(client, api_headers, isbn="0-8044-2957-x")
    assert b["isbn"] == "080442957X"


def test_duplicate_isbn_hyphenated(client, api_headers):
    make(client, api_headers)
    r = client.post("/books", json=body(isbn=ISBN13_PLAIN), headers=api_headers)
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "duplicate_isbn"


@pytest.mark.parametrize(
    "kw,field",
    [
        ({"isbn": "9780306406158"}, "isbn"),
        ({"isbn": "abc"}, "isbn"),
        ({"published_year": 1449}, "published_year"),
        ({"published_year": 9999}, "published_year"),
        ({"copies": -1}, "copies"),
    ],
)
def test_validation(client, api_headers, kw, field):
    r = client.post("/books", json=body(**kw), headers=api_headers)
    assert r.status_code == 422
    err = r.json()["error"]
    assert err["code"] == "validation_error"
    assert any(field in d["loc"] for d in err["details"])


def test_year_bounds_ok(client, api_headers):
    make(client, api_headers, published_year=1450)
    make(client, api_headers, isbn=ISBN10, published_year=datetime.now(UTC).year)


def test_put_patch(client, api_headers):
    b = make(client, api_headers)
    r = client.put(f"/books/{b['id']}", json=body(title="New", copies=5), headers=api_headers)
    assert r.status_code == 200 and r.json()["title"] == "New"
    r = client.patch(f"/books/{b['id']}", json={"copies": 1}, headers=api_headers)
    assert r.json()["copies"] == 1 and r.json()["title"] == "New"
    r = client.patch(f"/books/{b['id']}", json={"isbn": "bad"}, headers=api_headers)
    assert r.status_code == 422


def test_update_duplicate_isbn(client, api_headers):
    make(client, api_headers)
    other = make(client, api_headers, isbn=ISBN10)
    r = client.patch(f"/books/{other['id']}", json={"isbn": ISBN13}, headers=api_headers)
    assert r.status_code == 409 and r.json()["error"]["code"] == "duplicate_isbn"
    r = client.put(f"/books/{other['id']}", json=body(isbn=ISBN10), headers=api_headers)
    assert r.status_code == 200


def test_delete_and_404(client, api_headers):
    b = make(client, api_headers)
    assert client.delete(f"/books/{b['id']}", headers=api_headers).status_code == 204
    r = client.get(f"/books/{b['id']}")
    assert r.status_code == 404 and r.json()["error"]["code"] == "not_found"
    for method in (client.put, client.patch):
        assert method("/books/999", json=body(), headers=api_headers).status_code == 404
    assert client.delete("/books/999", headers=api_headers).status_code == 404


def test_search_and_paging(client, api_headers):
    make(client, api_headers, title="Tolkien Letters", author="Someone")
    make(client, api_headers, isbn=ISBN10, title="Hobbit", author="J. Tolkien")
    make(client, api_headers, isbn="9780306406164", title="Other", author="Nobody")
    r = client.get("/books", params={"q": "tolk"}).json()
    assert r["total"] == 2
    assert [i["title"] for i in r["items"]] == ["Hobbit", "Tolkien Letters"]
    r = client.get("/books", params={"q": "TOLK", "limit": 1, "offset": 1}).json()
    assert r["total"] == 2 and len(r["items"]) == 1 and r["items"][0]["title"] == "Tolkien Letters"
    assert client.get("/books").json()["total"] == 3
    assert client.get("/books", params={"limit": 0}).status_code == 422
    assert client.get("/books", params={"limit": 101}).status_code == 422


def test_available_copies_and_rules(client, api_headers, session):
    b = make(client, api_headers, copies=2)
    add_loan(session, b["id"])
    add_loan(session, b["id"], returned=True)
    assert client.get(f"/books/{b['id']}").json()["available_copies"] == 1
    r = client.patch(f"/books/{b['id']}", json={"copies": 0}, headers=api_headers)
    assert r.status_code == 409 and r.json()["error"]["code"] == "copies_below_open_loans"
    r = client.put(f"/books/{b['id']}", json=body(copies=0), headers=api_headers)
    assert r.status_code == 409
    r = client.delete(f"/books/{b['id']}", headers=api_headers)
    assert r.status_code == 409 and r.json()["error"]["code"] == "has_open_loans"


def test_delete_removes_returned_loans(client, api_headers, session):
    b = make(client, api_headers)
    add_loan(session, b["id"], returned=True)
    assert client.delete(f"/books/{b['id']}", headers=api_headers).status_code == 204
    assert session.query(Loan).count() == 0


@pytest.mark.parametrize("headers", [{}, {"X-API-Key": "wrong"}])
def test_unauthorized_changes_nothing(client, api_headers, headers):
    b = make(client, api_headers)
    calls = [
        client.post("/books", json=body(isbn=ISBN10), headers=headers),
        client.put(f"/books/{b['id']}", json=body(title="X"), headers=headers),
        client.patch(f"/books/{b['id']}", json={"title": "X"}, headers=headers),
        client.delete(f"/books/{b['id']}", headers=headers),
    ]
    for r in calls:
        assert r.status_code == 401 and r.json()["error"]["code"] == "unauthorized"
    assert client.get(f"/books/{b['id']}").json() == b
    assert client.get("/books").json()["total"] == 1
