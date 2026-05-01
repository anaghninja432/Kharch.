from fastapi import APIRouter, HTTPException, Query, status
from typing import Optional, Literal
from decimal import Decimal
import uuid

from database import get_connection
from schemas import ExpenseCreate, ExpenseOut, ExpenseListResponse

router = APIRouter()


def _row_to_out(row) -> ExpenseOut:
    """Convert a sqlite3.Row to ExpenseOut, converting paise → INR."""
    return ExpenseOut(
        id=row["id"],
        amount=Decimal(row["amount"]) / 100,
        category=row["category"],
        description=row["description"],
        date=row["date"],
        created_at=row["created_at"],
    )


@router.post(
    "",
    response_model=ExpenseOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new expense",
    description=(
        "Creates a new expense. Supply an `idempotency_key` (e.g. a UUID generated "
        "client-side) to make the request safe to retry: if the same key is received "
        "again, the original expense is returned with HTTP 200 instead of 201."
    ),
)
def create_expense(payload: ExpenseCreate):
    expense_id = str(uuid.uuid4())
    # Store amount as integer paise to avoid floating-point representation errors
    amount_paise = int(payload.amount * 100)

    with get_connection() as conn:
        # Idempotency: if a key was provided, check for an existing record first
        if payload.idempotency_key:
            existing = conn.execute(
                "SELECT * FROM expenses WHERE idempotency_key = ?",
                (payload.idempotency_key,),
            ).fetchone()
            if existing:
                # Return the previously created record; caller treats this as success
                from fastapi.responses import JSONResponse
                out = _row_to_out(existing)
                return JSONResponse(
                    content=out.model_dump(),
                    status_code=status.HTTP_200_OK,
                )

        try:
            conn.execute(
                """
                INSERT INTO expenses (id, idempotency_key, amount, category, description, date)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    expense_id,
                    payload.idempotency_key,
                    amount_paise,
                    payload.category,
                    payload.description,
                    payload.date.isoformat(),
                ),
            )
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Database error: {exc}")

        row = conn.execute(
            "SELECT * FROM expenses WHERE id = ?", (expense_id,)
        ).fetchone()

    return _row_to_out(row)


@router.get(
    "",
    response_model=ExpenseListResponse,
    summary="List expenses",
    description="Returns expenses with optional category filter and date-desc sorting.",
)
def list_expenses(
    category: Optional[str] = Query(None, description="Filter by category"),
    sort: Optional[Literal["date_desc", "date_asc"]] = Query(None, description="Sort order"),
):
    query = "SELECT * FROM expenses WHERE 1=1"
    params: list = []

    if category:
        query += " AND category = ?"
        params.append(category.strip().lower())

    if sort == "date_desc":
        query += " ORDER BY date DESC, created_at DESC"
    elif sort == "date_asc":
        query += " ORDER BY date ASC, created_at ASC"
    else:
        query += " ORDER BY created_at DESC"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()

    expenses = [_row_to_out(r) for r in rows]
    total = sum(e.amount for e in expenses)

    return ExpenseListResponse(data=expenses, total=total, count=len(expenses))