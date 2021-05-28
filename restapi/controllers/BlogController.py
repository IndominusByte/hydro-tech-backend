from config import database
from sqlalchemy.sql import select, func
from models.BlogModel import blog
from libs.Pagination import Pagination

class BlogLogic:
    pass

class BlogCrud:
    @staticmethod
    async def create_blog(**kwargs) -> int:
        return await database.execute(query=blog.insert(),values=kwargs)

    @staticmethod
    async def update_blog(id_: int, **kwargs) -> None:
        kwargs.update({"updated_at": func.now()})
        await database.execute(query=blog.update().where(blog.c.id == id_),values=kwargs)

    @staticmethod
    async def delete_blog(id_: int) -> None:
        await database.execute(query=blog.delete().where(blog.c.id == id_))

class BlogFetch:
    @staticmethod
    async def get_all_blog_paginate(**kwargs) -> dict:
        blog_alias = select([blog]).apply_labels().alias()

        query = select([blog_alias])

        if q := kwargs['q']:
            query = query.where(blog_alias.c.blogs_title.ilike(f"%{q}%"))
        if kwargs['order_by'] == 'newest':
            query = query.order_by(blog_alias.c.blogs_id.desc())
        if kwargs['order_by'] == 'oldest':
            query = query.order_by(blog_alias.c.blogs_id.asc())
        if kwargs['order_by'] == 'visitor':
            query = query.order_by(blog_alias.c.blogs_visitor.desc())

        total = await database.execute(query=select([func.count()]).select_from(query.alias()).as_scalar())
        query = query.limit(kwargs['per_page']).offset((kwargs['page'] - 1) * kwargs['per_page'])
        blog_db = await database.fetch_all(query=query)

        paginate = Pagination(kwargs['page'], kwargs['per_page'], total, blog_db)
        return {
            "data": [{index:value for index,value in item.items()} for item in paginate.items],
            "total": paginate.total,
            "next_num": paginate.next_num,
            "prev_num": paginate.prev_num,
            "page": paginate.page,
            "iter_pages": [x for x in paginate.iter_pages()]
        }

    @staticmethod
    async def filter_by_id(id_: int) -> blog:
        query = select([blog]).where(blog.c.id == id_)
        return await database.fetch_one(query=query)

    @staticmethod
    async def filter_by_slug(slug: str) -> blog:
        query = select([blog]).where(blog.c.slug == slug)
        return await database.fetch_one(query=query)
