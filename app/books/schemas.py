from datetime import UTC, datetime

from pydantic import BaseModel, Field, field_validator


def _isbn10_ok(s: str) -> bool:
    if len(s) != 10 or not s[:9].isdigit() or not (s[9].isdigit() or s[9] == "X"):
        return False
    total = sum((10 - i) * int(c) for i, c in enumerate(s[:9]))
    total += 10 if s[9] == "X" else int(s[9])
    return total % 11 == 0


def _isbn13_ok(s: str) -> bool:
    if len(s) != 13 or not s.isdigit():
        return False
    total = sum(int(c) * (1 if i % 2 == 0 else 3) for i, c in enumerate(s))
    return total % 10 == 0


def normalize_isbn(value: str) -> str:
    """Strip hyphens/spaces, upper-case, and verify the ISBN-10 or ISBN-13 checksum."""
    s = value.replace("-", "").replace(" ", "").upper()
    if not (_isbn10_ok(s) or _isbn13_ok(s)):
        raise ValueError("isbn must be a valid ISBN-10 or ISBN-13")
    return s


def _check_year(value: int) -> int:
    current = datetime.now(UTC).year
    if not 1450 <= value <= current:
        raise ValueError(f"published_year must be between 1450 and {current}")
    return value


class _BookValidators(BaseModel):
    @field_validator("isbn", check_fields=False)
    @classmethod
    def _isbn(cls, v: str | None) -> str | None:
        return None if v is None else normalize_isbn(v)

    @field_validator("published_year", check_fields=False)
    @classmethod
    def _year(cls, v: int | None) -> int | None:
        return None if v is None else _check_year(v)


class BookCreate(_BookValidators):
    title: str = Field(min_length=1, max_length=300)
    author: str = Field(min_length=1, max_length=200)
    isbn: str
    published_year: int
    copies: int = Field(ge=0)


class BookUpdate(_BookValidators):
    title: str | None = Field(None, min_length=1, max_length=300)
    author: str | None = Field(None, min_length=1, max_length=200)
    isbn: str | None = None
    published_year: int | None = None
    copies: int | None = Field(None, ge=0)


class BookOut(BaseModel):
    title: str
    author: str
    isbn: str
    published_year: int
    copies: int
    id: int
    available_copies: int
