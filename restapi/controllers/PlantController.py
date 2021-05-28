from config import database
from sqlalchemy.sql import select, func
from models.PlantModel import plant
from libs.Pagination import Pagination

class PlantLogic:
    pass

class PlantCrud:
    @staticmethod
    async def create_plant(**kwargs) -> int:
        return await database.execute(query=plant.insert(),values=kwargs)

    @staticmethod
    async def update_plant(id_: int, **kwargs) -> None:
        kwargs.update({"updated_at": func.now()})
        await database.execute(query=plant.update().where(plant.c.id == id_),values=kwargs)

    @staticmethod
    async def delete_plant(id_: int) -> None:
        await database.execute(query=plant.delete().where(plant.c.id == id_))

class PlantFetch:
    @staticmethod
    async def get_all_plants_paginate(**kwargs) -> dict:
        plant_alias = select([plant]).apply_labels().alias()

        query = select([plant_alias])

        if q := kwargs['q']:
            query = query.where(plant_alias.c.plants_name.ilike(f"%{q}%"))
        if difficulty := kwargs['difficulty']:
            query = query.where(plant_alias.c.plants_difficulty_level == difficulty)

        total = await database.execute(query=select([func.count()]).select_from(query.alias()).as_scalar())
        query = query.limit(kwargs['per_page']).offset((kwargs['page'] - 1) * kwargs['per_page'])
        plant_db = await database.fetch_all(query=query)

        paginate = Pagination(kwargs['page'], kwargs['per_page'], total, plant_db)
        return {
            "data": [{index:value for index,value in item.items()} for item in paginate.items],
            "total": paginate.total,
            "next_num": paginate.next_num,
            "prev_num": paginate.prev_num,
            "page": paginate.page,
            "iter_pages": [x for x in paginate.iter_pages()]
        }

    @staticmethod
    async def filter_by_name(name: str) -> plant:
        query = select([plant]).where(plant.c.name == name)
        return await database.fetch_one(query=query)

    @staticmethod
    async def filter_by_id(id_: int) -> plant:
        query = select([plant]).where(plant.c.id == id_)
        return await database.fetch_one(query=query)
