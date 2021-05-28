from config import database
from sqlalchemy.sql import select
from models.DocumentationModel import documentation
from models.CategoryDocModel import category_doc
from typing import Optional

class DocumentationLogic:
    pass

class DocumentationCrud:
    @staticmethod
    async def create_documentation(**kwargs) -> int:
        return await database.execute(query=documentation.insert(),values=kwargs)

    @staticmethod
    async def update_documentation(id_: int, **kwargs) -> None:
        await database.execute(query=documentation.update().where(documentation.c.id == id_),values=kwargs)

    @staticmethod
    async def delete_documentation(id_: int) -> None:
        await database.execute(query=documentation.delete().where(documentation.c.id == id_))

class DocumentationFetch:
    @staticmethod
    async def get_all_documentations(q: Optional[str]) -> category_doc:
        query = select([documentation.join(category_doc)]).order_by(documentation.c.category_doc_id) \
            .apply_labels()

        if q: query = query.where(documentation.c.title.ilike(f"%{q}%"))

        return await database.fetch_all(query=query)

    @staticmethod
    async def search_documentations_by_name(q: str, limit: int) -> list:
        query = select([documentation.join(category_doc)]).order_by(documentation.c.category_doc_id) \
            .where(
                (documentation.c.title.ilike(f"%{q}%")) |
                (documentation.c.description.ilike(f"%{q}%")) |
                (category_doc.c.name.ilike(f"%{q}%"))).limit(limit).apply_labels()

        documentation_db = await database.fetch_all(query=query)
        return [{index:value for index,value in item.items()} for item in documentation_db]

    @staticmethod
    async def filter_by_id(id_: int) -> documentation:
        query = select([documentation]).where(documentation.c.id == id_)
        return await database.fetch_one(query=query)

    @staticmethod
    async def filter_by_slug(slug: str) -> documentation:
        query = select([documentation.join(category_doc)]).where(documentation.c.slug == slug).apply_labels()
        return await database.fetch_one(query=query)
