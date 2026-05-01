from pydantic import BaseModel, Field, field_validator, model_validator
from decimal import Decimal
from typing import Optional
from datetime import date as DateType
import re


VALID_CATEGORIES = {
    "food", "transport", "housing", "utilities", "healthcare",
    "entertainment", "education", "shopping", "travel", "other"
}


class ExpenseCreate(BaseModel):
    amount: Decimal = Field(..., gt=0, decimal_places=2, description="Amount in INR (e.g. 199.99)")
    category: str = Field(..., min_length=1, max_length=50)
    description: str = Field(..., min_length=1, max_length=500)
    date: DateType
    idempotency_key: Optional[str] = Field(
        None,
        max_length=128,
        description="Client-supplied key to make POST idempotent (UUID recommended). "
                    "If the same key is received again, the original expense is returned."
    )

    @field_validator("category")
    @classmethod
    def normalize_category(cls, v: str) -> str:
        normalized = v.strip().lower()
        if normalized not in VALID_CATEGORIES:
            raise ValueError(
                f"Invalid category '{v}'. Must be one of: {', '.join(sorted(VALID_CATEGORIES))}"
            )
        return normalized

    @field_validator("description")
    @classmethod
    def strip_description(cls, v: str) -> str:
        return v.strip()


class ExpenseOut(BaseModel):
    id: str
    amount: Decimal          # returned in INR, converted back from paise
    category: str
    description: str
    date: str                # YYYY-MM-DD
    created_at: str          # ISO-8601 UTC

    model_config = {"from_attributes": True}


class ExpenseListResponse(BaseModel):
    data: list[ExpenseOut]
    total: Decimal           # sum of current filtered list
    count: int