from config import database
from sqlalchemy.sql import select, func
from models.GrowthPlantModel import growth_plant
from datetime import datetime, timedelta
from pytz import timezone
from config import settings

tz = timezone(settings.timezone)

class GrowthPlantLogic:
    pass

class GrowthPlantCrud:
    @staticmethod
    async def create_growth_plant(**kwargs) -> int:
        return await database.execute(query=growth_plant.insert(),values=kwargs)

    @staticmethod
    async def delete_growth_plant(user_id: int) -> None:
        await database.execute(query=growth_plant.delete().where(growth_plant.c.user_id == user_id))

class GrowthPlantFetch:
    @staticmethod
    async def get_recent_plant_image(user_id: int) -> growth_plant:
        query = select([growth_plant]).where(growth_plant.c.user_id == user_id).order_by(growth_plant.c.id.desc())
        return await database.fetch_one(query=query)

    @staticmethod
    async def get_growth_plant_chart_report(user_id: int, order_by: str) -> list:
        query = select([func.avg(growth_plant.c.height).label('avg'), growth_plant.c.user_id]) \
            .where((growth_plant.c.user_id == user_id) & (growth_plant.c.height != 0)).group_by(growth_plant.c.user_id)

        time_now = datetime.now(tz).replace(tzinfo=None)

        report_data = list()

        if order_by == '7day':
            for i in range(7):
                days_ago = time_now - timedelta(days=i)
                data = {'avg': 0.0, 'date': days_ago.strftime("%d %b %Y"), 'user_id': user_id}
                report_db = await database.fetch_one(query=query.where(func.date(growth_plant.c.created_at) == days_ago))

                if data_db := report_db: data.update(**{index:value for index,value in data_db.items()})
                report_data.append(data)

        if order_by == '30day':
            for i in range(1,5):
                days_ago = time_now - timedelta(days=i * 7)
                days_now = time_now - timedelta(days=i * 7 - 7)
                data = {
                    'avg': 0.0,
                    'date': '{} - {}'.format(days_ago.strftime("%d %b %Y"),days_now.strftime("%d %b %Y")),
                    'user_id': user_id
                }

                report_db = await database.fetch_one(query=query.where(
                    (func.date(growth_plant.c.created_at) >= days_ago) &
                    (func.date(growth_plant.c.created_at) <= days_now)
                ))

                if data_db := report_db: data.update(**{index:value for index,value in data_db.items()})
                report_data.append(data)

        return report_data
