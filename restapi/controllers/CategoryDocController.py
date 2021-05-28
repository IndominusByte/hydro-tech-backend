from config import database
from sqlalchemy.sql import select
from models.CategoryDocModel import category_doc
from typing import Optional

class CategoryDocLogic:
    pass

class CategoryDocCrud:
    @staticmethod
    async def create_category_doc(name: str) -> int:
        return await database.execute(query=category_doc.insert(),values={'name': name})

    @staticmethod
    async def update_category_doc(id_: int, **kwargs) -> None:
        await database.execute(query=category_doc.update().where(category_doc.c.id == id_),values=kwargs)

    @staticmethod
    async def delete_category_doc(id_: int) -> None:
        await database.execute(query=category_doc.delete().where(category_doc.c.id == id_))

class CategoryDocFetch:
    @staticmethod
    async def get_all_category_docs(q: Optional[str]) -> category_doc:
        query = select([category_doc]).order_by(category_doc.c.id.desc()).apply_labels()
        if q: query = query.where(category_doc.c.name.ilike(f"%{q}%"))

        return await database.fetch_all(query=query)

    @staticmethod
    async def filter_by_name(name: str) -> category_doc:
        query = select([category_doc]).where(category_doc.c.name == name)
        return await database.fetch_one(query=query)

    @staticmethod
    async def filter_by_id(id_: int) -> category_doc:
        query = select([category_doc]).where(category_doc.c.id == id_)
        return await database.fetch_one(query=query)
