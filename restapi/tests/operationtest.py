import pytest, bcrypt, os
from config import database
from sqlalchemy.sql import select
from datetime import datetime
from models.UserModel import user
from models.ConfirmationModel import confirmation
from models.PasswordResetModel import password_reset
from models.SettingUserModel import setting_user
from models.GrowthPlantModel import growth_plant
from models.PlantModel import plant
from models.ReportModel import report
from models.ChatModel import chat
from models.BlogModel import blog
from models.CategoryDocModel import category_doc
from models.DocumentationModel import documentation

class OperationTest:
    name = 'testtesttttttt'
    name2 = 'testtesttttttt2'
    account_1 = {'email':'testtesting@gmail.com','username':'testtesting','password':'testtesting'}
    account_2 = {'email':'testtesting2@gmail.com','username':'testtesting2','password':'testtesting2'}
    base_dir = os.path.join(os.path.dirname(__file__),'../static/')
    test_image_dir = base_dir + 'test_image/'
    avatar_dir = base_dir + 'avatars/'
    plant_dir = base_dir + 'plants/'
    blog_dir = base_dir + 'blogs/'

    # ================ USER SECTION ================

    @pytest.mark.asyncio
    async def get_user_avatar(self,email: str):
        user_data = await database.fetch_one(query=select([user]).where(user.c.email == email))
        return user_data['avatar']

    @pytest.mark.asyncio
    async def set_user_to_admin(self,email: str):
        await database.execute(query=user.update().where(user.c.email == email),values={'role': 'admin'})

    """
    @pytest.mark.asyncio
    async def set_user_to_guest(self,email: str):
        await database.execute(query=user.update().where(user.c.email == email),values={'role': 'guest'})
    """

    @pytest.mark.asyncio
    async def reset_password_user_to_default(self,email: str):
        query = user.update().where(user.c.email == email)
        password = self.account_1['password'] if email == self.account_1['email'] else self.account_2['password']
        hashed_pass = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        await database.execute(query=query,values={"password": hashed_pass.decode('utf-8')})

    @pytest.mark.asyncio
    async def delete_password_user(self,email: str):
        query = user.update().where(user.c.email == email)
        await database.execute(query=query,values={"password": None})

    @pytest.mark.asyncio
    async def add_password_user(self,email: str, password: str):
        query = user.update().where(user.c.email == email)
        hashed_pass = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        await database.execute(query=query,values={"password": hashed_pass.decode('utf-8')})

    @pytest.mark.asyncio
    async def get_confirmation(self, email: str):
        user_data = await database.fetch_one(query=select([user]).where(user.c.email == email))
        confirm = await database.fetch_one(query=select([confirmation]).where(confirmation.c.user_id == user_data['id']))
        return confirm['id']

    @pytest.mark.asyncio
    async def set_account_to_activated(self, id_: str):
        query = confirmation.update().where(confirmation.c.id == id_)
        await database.execute(query=query,values={"activated": True})

    @pytest.mark.asyncio
    async def set_account_to_unactivated(self, id_: str):
        query = confirmation.update().where(confirmation.c.id == id_)
        await database.execute(query=query,values={"activated": False})

    @pytest.mark.asyncio
    async def set_account_to_unexpired(self, id_: str):
        confirm = await database.fetch_one(query=select([confirmation]).where(confirmation.c.id == id_))
        query = confirmation.update().where(confirmation.c.id == id_)
        await database.execute(query=query,values={"resend_expired": confirm['resend_expired'] - 300})  # decrease 5 minute

    @pytest.mark.asyncio
    async def decrease_password_reset(self, email: str):
        reset = await database.fetch_one(query=select([password_reset]).where(password_reset.c.email == email))
        query = password_reset.update().where(password_reset.c.email == email)
        await database.execute(query=query,values={"resend_expired": reset['resend_expired'] - 300})  # decrease 5 minute

    @pytest.mark.asyncio
    async def get_password_reset(self, email: str):
        reset = await database.fetch_one(query=select([password_reset]).where(password_reset.c.email == email))
        return reset['id']

    @pytest.mark.asyncio
    async def get_user_id(self, email: str):
        user_data = await database.fetch_one(query=select([user]).where(user.c.email == email))
        return user_data['id']

    @pytest.mark.asyncio
    async def delete_user_from_db(self):
        # delete user 1
        query = user.delete().where(user.c.email == self.account_1['email'])
        await database.execute(query=query)
        # delete user 2
        query = user.delete().where(user.c.email == self.account_2['email'])
        await database.execute(query=query)

    # ================ PLANT SECTION ================

    @pytest.mark.asyncio
    async def get_plant_image(self,name: str):
        query = select([plant]).where(plant.c.name == name)
        plant_data = await database.fetch_one(query=query)
        return plant_data['image']

    @pytest.mark.asyncio
    async def get_plant_id(self,name: str):
        query = select([plant]).where(plant.c.name == name)
        plant_data = await database.fetch_one(query=query)
        return plant_data['id']

    # ================ SETTING USER SECTION ================

    @pytest.mark.asyncio
    async def delete_setting_user(self,email: str):
        user_id = await self.get_user_id(email)
        query = setting_user.delete().where(setting_user.c.user_id == user_id)
        await database.execute(query=query)

    @pytest.mark.asyncio
    async def set_planted_to_true_false(self,email: str, planted: bool):
        user_id = await self.get_user_id(email)
        query = setting_user.update().where(setting_user.c.user_id == user_id)
        await database.execute(query=query,values={'planted': planted})

    @pytest.mark.asyncio
    async def set_planted_at(self,email: str, planted_at: datetime):
        user_id = await self.get_user_id(email)
        query = setting_user.update().where(setting_user.c.user_id == user_id)
        await database.execute(query=query,values={'planted_at': planted_at})

    # ================ REPORT SECTION ================

    @pytest.mark.asyncio
    async def create_report(self,email: str):
        user_id = await self.get_user_id(email)
        data = {'ph': 7.57, 'tds': 392.34, 'temp': 25.63, 'ldr': 'bright', 'tank': 69, 'user_id': user_id}
        await database.execute(query=report.insert(),values=data)

    # ================ GROWTH PLANT SECTION ================

    @pytest.mark.asyncio
    async def get_recent_height(self,email: str):
        user_id = await self.get_user_id(email)
        query = select([growth_plant]).where(growth_plant.c.user_id == user_id).order_by(growth_plant.c.id.desc())
        growth_plant_data = await database.fetch_one(query=query)
        return growth_plant_data['height']

    # ================ CHAT SECTION ================

    @pytest.mark.asyncio
    async def create_chat(self,email: str):
        user_id = await self.get_user_id(email)
        data = {'message': 'hello', 'user_id': user_id}
        await database.execute(query=chat.insert(),values=data)

    # ================ BLOG SECTION ================

    @pytest.mark.asyncio
    async def get_blog_image(self,title: str):
        query = select([blog]).where(blog.c.title == title)
        blog_data = await database.fetch_one(query=query)
        return blog_data['image']

    @pytest.mark.asyncio
    async def get_blog_id(self,title: str):
        query = select([blog]).where(blog.c.title == title)
        blog_data = await database.fetch_one(query=query)
        return blog_data['id']

    # ================ CATEGORY DOC SECTION ================

    @pytest.mark.asyncio
    async def get_category_doc_id(self,name: str):
        query = select([category_doc]).where(category_doc.c.name == name)
        category_doc_data = await database.fetch_one(query=query)
        return category_doc_data['id']

    # ================ DOCUMENTATION SECTION ================

    @pytest.mark.asyncio
    async def get_documentation_id(self,title: str):
        query = select([documentation]).where(documentation.c.title == title)
        documentation_data = await database.fetch_one(query=query)
        return documentation_data['id']
