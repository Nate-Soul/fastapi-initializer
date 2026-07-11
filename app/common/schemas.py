from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict = {}


class ErrorResponse(BaseModel):
    error: ErrorBody


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int
