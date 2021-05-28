from config import database
from sqlalchemy.sql import select, func
from models.SettingUserModel import setting_user
from models.PlantModel import plant
from datetime import datetime
from pytz import timezone
from config import settings

tz = timezone(settings.timezone)

class SettingUserLogic:
    pass

class SettingUserCrud:
    @staticmethod
    async def create_setting_user(**kwargs) -> int:
        return await database.execute(query=setting_user.insert(),values=kwargs)

    @staticmethod
    async def update_setting_user(user_id: int, **kwargs) -> None:
        await database.execute(query=setting_user.update().where(setting_user.c.user_id == user_id),values=kwargs)

    @staticmethod
    async def change_setting_plants_status(user_id: int, planted: bool) -> None:
        query = setting_user.update().where(setting_user.c.user_id == user_id)
        await database.execute(query=query,values={'planted': planted, 'planted_at': func.now()})

class SettingUserFetch:
    @staticmethod
    async def get_progress_plant(user_id: int) -> dict:
        query = select([setting_user.join(plant)]).where(setting_user.c.user_id == user_id).apply_labels()
        progress_db = await database.fetch_one(query=query)

        if progress_db := progress_db:
            progress_data = {index:value for index,value in progress_db.items()}
            if progress_data['setting_users_planted'] is False:
                return {'percentage': 0}

            days = progress_data['plants_growth_value']
            days_total = days if progress_data['plants_growth_type'] == 'days' else 7 * days

            time_now = datetime.now(tz).replace(tzinfo=None)
            days_between = (time_now - progress_data['setting_users_planted_at']).days
            percentage = round((days_between / days_total) * 100)
            percentage = percentage if percentage <= 100 else 100

            return {'percentage': percentage}
        return {'percentage': 0}

    @staticmethod
    async def get_my_setting(user_id: int) -> None:
        query = select([setting_user.join(plant)]).where(setting_user.c.user_id == user_id).apply_labels()
        return await database.fetch_one(query=query)

    @staticmethod
    async def filter_by_user_id(user_id: int) -> setting_user:
        query = select([setting_user]).where(setting_user.c.user_id == user_id)
        return await database.fetch_one(query=query)
