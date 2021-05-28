from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class ChatSchema(BaseModel):
    class Config:
        min_anystr_length = 1
        anystr_strip_whitespace = True

class ChatData(ChatSchema):
    chats_id: str
    chats_message: str
    chats_created_at: datetime
    users_id: str
    users_username: str
    users_avatar: str

class ChatPaginate(ChatSchema):
    data: List[ChatData]
    total: int
    next_num: Optional[int]
    prev_num: Optional[int]
    page: int
    iter_pages: list
