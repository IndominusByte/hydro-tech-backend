from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class BlogSchema(BaseModel):
    class Config:
        min_anystr_length = 1
        anystr_strip_whitespace = True

class BlogData(BlogSchema):
    blogs_id: int
    blogs_title: str
    blogs_slug: str
    blogs_image: str
    blogs_description: str
    blogs_visitor: str
    blogs_created_at: datetime
    blogs_updated_at: datetime

class BlogPaginate(BlogSchema):
    data: List[BlogData]
    total: int
    next_num: Optional[int]
    prev_num: Optional[int]
    page: int
    iter_pages: list
