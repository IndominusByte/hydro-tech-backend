from config import database
from sqlalchemy.sql import select, exists, func
from models.AlertModel import alert
from typing import Optional
from datetime import datetime, timedelta
from pytz import timezone
from config import settings

tz = timezone(settings.timezone)

class AlertLogic:
    @staticmethod
    async def check_alert(user_id: int, _type: str, msg: Optional[str] = None) -> bool:
        if msg is None:
            query = select([exists().where((alert.c.user_id == user_id) & (alert.c.type == _type))]).as_scalar()
        else:
            query = select([exists().where(
                (alert.c.user_id == user_id) &
                (alert.c.type == _type) &
                (alert.c.message == msg)
            )]).as_scalar()

        return await database.execute(query=query)

class AlertCrud:
    @staticmethod
    async def create_alert(**kwargs) -> int:
        return await database.execute(query=alert.insert(),values=kwargs)

    @staticmethod
    async def delete_alert(user_id: int) -> None:
        await database.execute(query=alert.delete().where(alert.c.user_id == user_id))

class AlertFetch:
    @staticmethod
    async def filter_by_user_id(user_id: int) -> alert:
        query = select([alert]).where(alert.c.user_id == user_id)
        return await database.fetch_one(query=query)

    @staticmethod
    async def get_alert_report(user_id: int, order_by: str) -> list:
        query = select([alert]).where(alert.c.user_id == user_id).order_by(alert.c.id.desc())

        time_now = datetime.now(tz).replace(tzinfo=None)

        if order_by == 'today':
            query = query.where(func.date(alert.c.created_at) == time_now)
        if order_by == '3day':
            three_days_ago = time_now - timedelta(days=3)
            query = query.where(
                (func.date(alert.c.created_at) >= three_days_ago) &
                (func.date(alert.c.created_at) <= time_now)
            )
        if order_by == '7day':
            seven_days_ago = time_now - timedelta(days=7)
            query = query.where(
                (func.date(alert.c.created_at) >= seven_days_ago) &
                (func.date(alert.c.created_at) <= time_now)
            )

        alert_db = await database.fetch_all(query=query)
        alert_data = [{index:value for index,value in item.items()} for item in alert_db]

        return alert_data
