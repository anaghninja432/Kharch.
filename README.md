# Kharch — Expense Tracker

A minimal, production-grade expense tracker with a FastAPI backend and a standalone HTML/JS frontend.

---

## Quick Start

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

API will be live at **http://localhost:8000**
Interactive docs at **http://localhost:8000/docs**

### Frontend
Open `frontend/index.html` directly in your browser — no build step or server required.

On Linux:
```bash
xdg-open frontend/index.html
```
On macOS:
```bash
open frontend/index.html
```
On Windows, double-click the file or run:
```bash
start frontend/index.html
```

> Make sure the backend is running before opening the frontend, otherwise expenses won't load.

---

## Project Structure

```
expense-tracker/
├── backend/
│   ├── main.py            # FastAPI app, CORS, lifespan
│   ├── database.py        # SQLite init, connection helper
│   ├── schemas.py         # Pydantic request/response models
│   ├── routers/
│   │   └── expenses.py    # POST /expenses, GET /expenses
│   └── requirements.txt
└── frontend/
    └── index.html         # Single-file UI (no build step)
```

---

## API Reference

### `POST /expenses`
Create a new expense.

**Body:**
```json
{
  "amount": 199.50,
  "category": "food",
  "description": "Dinner at Swaad",
  "date": "2024-06-15",
  "idempotency_key": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Categories:** `food`, `transport`, `housing`, `utilities`, `healthcare`, `entertainment`, `education`, `shopping`, `travel`, `other`

**Idempotency:** If you include an `idempotency_key`, retrying the same request returns the original record (HTTP 200) instead of creating a duplicate. The client generates a UUID per submission attempt and reuses it on retries.

---

### `GET /expenses`
List all expenses.

| Query param | Description |
|---|---|
| `category` | Filter by category (e.g. `food`) |
| `sort=date_desc` | Sort by date newest-first |

**Response:**
```json
{
  "data": [...],
  "total": 3450.75,
  "count": 12
}
```

---

## Design Decisions

### Persistence: SQLite

**Why SQLite?**

- **Zero ops** — No separate database server to run, configure, or secure.
- **File-based** — The entire database is a single `expenses.db` file; trivial to back up or inspect with any SQLite browser.
- **More than adequate at this scale** — A personal finance tool has a single user and low concurrency. SQLite handles thousands of reads/writes per second comfortably, and WAL mode (`PRAGMA journal_mode=WAL`) enables concurrent reads without blocking writes.
- **Production-safe** — SQLite is used in production by many applications (Litestream, Fly.io volumes, etc.). It is not a "throwaway" choice.

If this were to grow into a multi-user SaaS, a migration to PostgreSQL would be straightforward since all SQL used here is standard.

### Money: Integer paise, not floats

Amounts are stored as **integers in paise** (1 INR = 100 paise) in the database. This eliminates floating-point rounding errors that accumulate when summing monetary values. The Pydantic schema accepts `Decimal` from the client, converts to `int` for storage, and converts back to `Decimal` for responses. This is the same approach used by Stripe, Square, and most payment APIs.

### Idempotency

`POST /expenses` accepts an optional `idempotency_key` (a UUID the client generates). The key is stored in a `UNIQUE` column. On retry:
- If the key exists → return the original record with HTTP 200 (safe for the client to treat as success).
- If not → insert normally and return HTTP 201.

This makes the endpoint safe to retry after network failures, page reloads, or client-side timeout/retry loops.

### Validation

Categories are validated against an explicit allowlist in Pydantic. The frontend enforces the same list via a `<select>`, but the API validates independently — never trust the client.

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DB_PATH` | `expenses.db` | Path to the SQLite database file |


## Another small note

There are multiple cases where this project might expose some shortcomings like : removing an expense or monthly/yearly/quarterly analytics (although this might be a feature in it's own). However I just wanted things to be as simple as I could possibly make right now within 4 hours, so I didn't add it. This repo is very simple in its own , using FastAPI (one of my most favourite libraries through and out for simple applications which are currently not data heavy) and the structure is pretty monotone, as I preferred for a simple get go site.

## Live Demo

Frontend (GitHub Pages):  
[https://anaghninja432.github.io/Kharch/](https://anaghninja432.github.io/Kharch./)

Backend (Render):  
https://kharch.onrender.com/

> Note: The backend is hosted on Render’s free tier and may take ~30–60 seconds to wake up after inactivity.
> If the app appears unresponsive, open the backend URL once to wake the service.

## Tech Stack

- Backend: FastAPI
- Database: SQLite (WAL mode)
- Frontend: Vanilla HTML/CSS/JS
- Deployment: GitHub Pages (frontend), Render (backend)
