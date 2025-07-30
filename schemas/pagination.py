from pydantic import BaseModel
from typing import List, Generic, TypeVar


T = TypeVar("T")


class Pagination(BaseModel):
    current_page_size: int
    current_page: int
    total_pages: int


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    pagination: Pagination
