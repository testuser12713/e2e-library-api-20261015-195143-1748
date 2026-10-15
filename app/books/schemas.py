from pydantic import BaseModel, Field


class BookCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    author: str = Field(min_length=1, max_length=200)
    isbn: str
    published_year: int
    copies: int = Field(ge=0)


class BookUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=300)
    author: str | None = Field(None, min_length=1, max_length=200)
    isbn: str | None = None
    published_year: int | None = None
    copies: int | None = Field(None, ge=0)


class BookOut(BookCreate):
    id: int
    available_copies: int
