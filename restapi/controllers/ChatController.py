from config import database
from sqlalchemy.sql import select, func
from models.ChatModel import chat
from models.UserModel import user
from libs.Pagination import Pagination

class ChatLogic:
    pass

class ChatCrud:
    @staticmethod
    async def create_chat(**kwargs) -> int:
        return await database.execute(query=chat.insert(),values=kwargs)

class ChatFetch:
    @staticmethod
    async def get_all_chats_paginate(**kwargs) -> dict:
        chat_alias = select([chat.join(user)]).distinct(chat.c.id).apply_labels().alias()

        query = select([chat_alias])

        if kwargs['order_by'] is None:
            query = query.order_by(chat_alias.c.chats_id.desc())
        if kwargs['order_by'] == 'longest':
            query = query.order_by(chat_alias.c.chats_id.asc())

        total = await database.execute(query=select([func.count()]).select_from(query.alias()).as_scalar())
        query = query.limit(kwargs['per_page']).offset((kwargs['page'] - 1) * kwargs['per_page'])
        chat_db = await database.fetch_all(query=query)

        paginate = Pagination(kwargs['page'], kwargs['per_page'], total, chat_db)
        return {
            "data": [{index:value for index,value in item.items()} for item in paginate.items],
            "total": paginate.total,
            "next_num": paginate.next_num,
            "prev_num": paginate.prev_num,
            "page": paginate.page,
            "iter_pages": [x for x in paginate.iter_pages()]
        }

    @staticmethod
    async def filter_by_id(id_: int) -> chat:
        query = select([chat.join(user)]).where(chat.c.id == id_).apply_labels()
        return await database.fetch_one(query=query)
