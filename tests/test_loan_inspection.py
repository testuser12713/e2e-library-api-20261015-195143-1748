from datetime import timedelta

from app.models import Loan


def _add(session, clock, **kw):
    now = clock.now
    d = {
        "book_id": 1,
        "member_id": 1,
        "loaned_at": now - timedelta(days=20),
        "due_at": now - timedelta(days=6, hours=5),
        "returned_at": None,
    }
    d.update(kw)
    loan = Loan(**d)
    session.add(loan)
    session.commit()
    return loan.id


def test_overdue_and_status(client, session, clock):
    now = clock.now
    a = _add(session, clock)
    r = _add(session, clock, returned_at=now - timedelta(days=1))
    f = _add(session, clock, due_at=now + timedelta(days=3))
    body = client.get("/loans/overdue").json()
    assert [i["id"] for i in body["items"]] == [a]
    assert body["items"][0]["days_overdue"] == 6
    assert body["total"] == 1
    op = [i["id"] for i in client.get("/loans?status=open").json()["items"]]
    assert op == [a, f]
    rt = [i["id"] for i in client.get("/loans?status=returned").json()["items"]]
    assert rt == [r]
    assert client.get("/loans?status=bogus").status_code == 422


def test_filters_pagination_ordering(client, session, clock):
    now = clock.now
    ids = [
        _add(
            session,
            clock,
            member_id=m,
            book_id=b,
            due_at=now - timedelta(days=d),
            loaned_at=now - timedelta(days=30 - d),
        )
        for m, b, d in [(1, 1, 3), (2, 1, 5), (1, 2, 4)]
    ]
    assert client.get("/loans?member_id=1").json()["total"] == 2
    assert client.get("/loans?book_id=2").json()["items"][0]["id"] == ids[2]
    page = client.get("/loans?limit=2&offset=1").json()
    assert page["total"] == 3 and len(page["items"]) == 2
    assert [i["id"] for i in client.get("/loans").json()["items"]] == [ids[0], ids[2], ids[1]]
    od = [i["id"] for i in client.get("/loans/overdue").json()["items"]]
    assert od == [ids[1], ids[2], ids[0]]


def test_get_loan(client, session, clock):
    lid = _add(session, clock)
    assert client.get(f"/loans/{lid}").json()["id"] == lid
    r = client.get("/loans/9999")
    assert r.status_code == 404
    err = r.json()["error"]
    assert err["code"] == "not_found" and "message" in err and "details" in err
