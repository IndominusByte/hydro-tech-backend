from config import database
from sqlalchemy.sql import select, func
from models.ReportModel import report
from datetime import datetime, timedelta
from pytz import timezone
from config import settings

tz = timezone(settings.timezone)

class ReportLogic:
    pass

class ReportCrud:
    @staticmethod
    async def create_report(**kwargs) -> int:
        return await database.execute(query=report.insert(),values=kwargs)

    @staticmethod
    async def delete_report(user_id: int) -> None:
        await database.execute(query=report.delete().where(report.c.user_id == user_id))
        # await database.execute(query="ALTER SEQUENCE reports_id_seq RESTART WITH 1")

class ReportFetch:
    @staticmethod
    async def get_all_reports(user_id: int, order_by: str) -> list:
        query = select([report]).where(report.c.user_id == user_id).order_by(report.c.id.desc())

        time_now = datetime.now(tz).replace(tzinfo=None)

        if order_by == 'today':
            query = query.where(func.date(report.c.created_at) == time_now)
        if order_by == '7day':
            seven_days_ago = time_now - timedelta(days=7)
            query = query.where(
                (func.date(report.c.created_at) >= seven_days_ago) &
                (func.date(report.c.created_at) <= time_now)
            )
        if order_by == '30day':
            thirty_days_ago = time_now - timedelta(days=30)
            query = query.where(
                (func.date(report.c.created_at) >= thirty_days_ago) &
                (func.date(report.c.created_at) <= time_now)
            )
        if order_by == '90day':
            ninety_days_ago = time_now - timedelta(days=90)
            query = query.where(
                (func.date(report.c.created_at) >= ninety_days_ago) &
                (func.date(report.c.created_at) <= time_now)
            )

        report_db = await database.fetch_all(query=query)
        report_data = [{index:value for index,value in item.items()} for item in report_db]

        return report_data

    @staticmethod
    async def get_chart_reports(user_id: int, order_by: str, chart: str) -> list:
        if chart == 'ph':
            query = select([func.avg(report.c.ph).label('avg'), report.c.user_id]) \
                .where(report.c.user_id == user_id).group_by(report.c.user_id)
        if chart == 'tds':
            query = select([func.avg(report.c.tds).label('avg'), report.c.user_id]) \
                .where(report.c.user_id == user_id).group_by(report.c.user_id)

        time_now = datetime.now(tz).replace(tzinfo=None)

        report_data = list()

        if order_by == '7day':
            for i in range(7):
                days_ago = time_now - timedelta(days=i)
                data = {'avg': 0.0, 'date': days_ago.strftime("%d %b %Y"), 'user_id': user_id}
                report_db = await database.fetch_one(query=query.where(func.date(report.c.created_at) == days_ago))

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
                    (func.date(report.c.created_at) >= days_ago) &
                    (func.date(report.c.created_at) <= days_now)
                ))

                if data_db := report_db: data.update(**{index:value for index,value in data_db.items()})
                report_data.append(data)

        return report_data
