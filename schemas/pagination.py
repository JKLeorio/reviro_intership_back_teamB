from pydantic import BaseModel


class Pagination(BaseModel):
    current_page_size: int
    current_page: int
    total_pages: int