# Ausleih-REST-API für die Stadtbibliothek

REST-API für den Ausleihtresen einer kleinen Stadtbibliothek: verwaltet Bücher, Mitglieder und Ausleihen, schützt alle schreibenden Endpunkte per `X-API-Key` und antwortet bei jedem Fehler mit demselben Fehlerformat. Hinweis: Dieser Stand ist das lauffähige Gerüst; die Fachlogik der Endpunkte außer `/health` liefern die folgenden Tickets (bis dahin antworten sie mit `501 not_implemented`).

## Tech-Stack

Python 3.12+, FastAPI, Pydantic v2 (+ pydantic-settings), SQLAlchemy 2, SQLite, uvicorn, pytest, ruff.

## Installation

```bash
pip install -r requirements.txt
```

## Starten

```bash
export LIBRARY_API_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
python -m uvicorn app.main:app --port 8000
```

Die Tabellen werden beim Start automatisch angelegt. Dokumentation: `http://localhost:8000/docs`.

## Umgebungsvariablen

| Variable | Pflicht | Beschreibung |
|---|---|---|
| `LIBRARY_API_KEY` | ja, für Schreibzugriffe | Schlüssel für den Header `X-API-Key`. Ohne Wert antworten Schreib-Endpunkte mit `503 api_key_not_configured`. Siehe `.env.example`. |
| `DATABASE_URL` | nein | Standard `sqlite:///./library.db` |

## Endpunkte

Schreibende Endpunkte (POST/PUT/PATCH/DELETE) brauchen den Header `X-API-Key`.

- `GET /health` -> `200 {"status": "ok"}`
- `POST /books`, `GET /books?q&limit&offset`, `GET|PUT|PATCH|DELETE /books/{book_id}`
- `POST /members`, `GET /members?limit&offset`, `GET|PUT|PATCH|DELETE /members/{member_id}`
- `POST /loans`, `POST /loans/{loan_id}/return`
- `GET /loans?member_id&book_id&status=open|returned|all&limit&offset`, `GET /loans/overdue`, `GET /loans/{loan_id}`

Fehlerformat: `{"error": {"code": "not_found", "message": "...", "details": null}}`. Listen liefern `{"items": [], "total": 0, "limit": 20, "offset": 0}`.

## Tests und Lint

```bash
python -m pytest
ruff format --check . && ruff check .
```

## Funktionen

- Health-Check mit Datenbankabfrage
- Einheitliches Fehlerformat (404, 405, 422, 500 ...)
- API-Key-Schutz für Schreibzugriffe (konstante Vergleichszeit)
- Paginierung, Zeitstempel in UTC, Schema-Anlage beim Start
