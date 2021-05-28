from fastapi import Query
from typing import Literal

def get_all_query_chat(
    page: int = Query(...,gt=0),
    per_page: int = Query(...,gt=0),
    order_by: Literal['longest'] = Query(None)
):
    return {
        "page": page,
        "per_page": per_page,
        "order_by": order_by
    }
