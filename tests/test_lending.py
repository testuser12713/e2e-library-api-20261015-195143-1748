from datetime import timedelta

from app.counts import open_loans_for_book
from app.models import Book, Member


def _seed(session, copies=1, members=1, books=1):
    bs = [
        Book(title=f"T{i}", author="A", isbn=f"97800000000{i}", published_year=2000, copies=copies)
        for i in range(books)
    ]
    ms = [
        Member(name=f"M{i}", email=f"m{i}@example.com", member_since=None) for i in range(members)
    ]
    for m in ms:
        m.member_since = __import__("datetime").date(2024, 1, 1)
    session.add_all(bs + ms)
    session.commit()
    return bs, ms


def _loan(client, h, b, m):
    return client.post("/loans", json={"book_id": b, "member_id": m}, headers=h)


def test_create_and_return(client, session, api_headers, clock):
    (b,), (m,) = _seed(session)
    r = _loan(client, api_headers, b.id, m.id)
    assert r.status_code == 201
    j = r.json()
    from datetime import datetime

    assert datetime.fromisoformat(j["due_at"]) - datetime.fromisoformat(
        j["loaned_at"]
    ) == timedelta(days=14)
    session.expire_all()
    assert open_loans_for_book(session, b.id) == 1
    clock.advance(timedelta(days=1))
    r2 = client.post(f"/loans/{j['id']}/return", headers=api_headers)
    assert r2.status_code == 200 and r2.json()["returned_at"]
    again = client.post(f"/loans/{j['id']}/return", headers=api_headers)
    assert again.status_code == 409 and again.json()["error"]["code"] == "already_returned"
    session.expire_all()
    assert open_loans_for_book(session, b.id) == 0


def test_limit_and_after_return(client, session, api_headers):
    bs, (m,) = _seed(session, copies=5, books=4)
    ids = [_loan(client, api_headers, b.id, m.id).json()["id"] for b in bs[:3]]
    r = _loan(client, api_headers, bs[3].id, m.id)
    assert r.status_code == 409 and r.json()["error"]["code"] == "loan_limit_reached"
    client.post(f"/loans/{ids[0]}/return", headers=api_headers)
    assert _loan(client, api_headers, bs[3].id, m.id).status_code == 201


def test_no_copy(client, session, api_headers):
    (b,), ms = _seed(session, copies=1, members=2)
    assert _loan(client, api_headers, b.id, ms[0].id).status_code == 201
    r = _loan(client, api_headers, b.id, ms[1].id)
    assert r.status_code == 409 and r.json()["error"]["code"] == "no_copy_available"


def test_unknown_ids(client, session, api_headers):
    (b,), (m,) = _seed(session)
    assert _loan(client, api_headers, 999, m.id).status_code == 404
    r = _loan(client, api_headers, b.id, 999)
    assert r.status_code == 404 and r.json()["error"]["code"] == "not_found"
    assert client.post("/loans/999/return", headers=api_headers).status_code == 404


def test_unauthorized(client, session):
    (b,), (m,) = _seed(session)
    r = client.post("/loans", json={"book_id": b.id, "member_id": m.id})
    assert r.status_code == 401 and r.json()["error"]["code"] == "unauthorized"
    session.expire_all()
    assert open_loans_for_book(session, b.id) == 0
    assert client.post("/loans/1/return", headers={"X-API-Key": "x"}).status_code == 401
