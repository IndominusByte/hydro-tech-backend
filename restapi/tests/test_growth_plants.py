import pytest
from pathlib import Path
from config import redis_conn, settings
from libs.MagicImage import MagicImage
from .operationtest import OperationTest

class TestGrowthPlant(OperationTest):
    prefix = "/growth-plants"
    iot_token = None

    @pytest.mark.asyncio
    async def test_add_user(self,async_client):
        url = '/users/register'
        # register user admin
        response = await async_client.post(url,
            json={
                'username': self.account_1['username'],
                'email': self.account_1['email'],
                'password': self.account_1['password'],
                'confirm_password': self.account_1['password']
            }
        )
        assert response.status_code == 201
        assert response.json() == {"detail":"Check your email to activated your account."}
        # activated the user admin
        confirm_id = await self.get_confirmation(self.account_1['email'])
        await self.set_account_to_activated(confirm_id)
        await self.set_user_to_admin(self.account_1['email'])

        # register user not admin
        response = await async_client.post(url,
            json={
                'username': self.account_2['username'],
                'email': self.account_2['email'],
                'password': self.account_2['password'],
                'confirm_password': self.account_2['password']
            }
        )
        assert response.status_code == 201
        assert response.json() == {"detail":"Check your email to activated your account."}
        # activated the user
        confirm_id = await self.get_confirmation(self.account_2['email'])
        await self.set_account_to_activated(confirm_id)

    @pytest.mark.asyncio
    async def test_create_plant(self,async_client):
        response = await async_client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': self.account_1['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = '/plants/create'

        with open(self.test_image_dir + 'image.jpeg','rb') as tmp:
            response = await async_client.post(url,
                data={
                    'name': self.name,
                    'desc': 'a' * 30,
                    'ph_max': '1.0',
                    'ph_min': '1.0',
                    'tds_min': '1.0',
                    'growth_value': '1',
                    'growth_type': 'days',
                    'difficulty_level': 'easy'
                },
                files={'image': tmp},
                headers={'X-CSRF-TOKEN': csrf_access_token}
            )
            assert response.status_code == 201
            assert response.json() == {"detail": "Successfully add a new plant."}

        # check image exists in directory
        image = await self.get_plant_image(self.name)
        assert Path(self.plant_dir + image).is_file() is True

    def test_create_iot_token(self,client):
        response = client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': self.account_1['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = '/users/create-iot-token'

        response = client.post(url,headers={"X-CSRF-TOKEN": csrf_access_token})
        assert response.status_code == 200
        # assign to variable
        self.__class__.iot_token = response.json()['token']

    @pytest.mark.asyncio
    async def test_create_setting_user(self,async_client):
        # user login
        response = await async_client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': self.account_1['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = '/setting-users/create'
        plant_id = await self.get_plant_id(self.name)

        response = await async_client.post(url,headers={"X-CSRF-TOKEN": csrf_access_token},json={
            'camera': True,
            'token': self.iot_token,
            'plant_id': str(plant_id)
        })
        assert response.status_code == 201
        assert response.json() == {"detail": "Successfully create an setting."}

    def test_validation_upload_image_camera(self,client):
        url = self.prefix + '/upload-image-camera'
        # danger file extension
        with open(self.test_image_dir + 'test.txt','rb') as tmp:
            response = client.post(url,files={'file': tmp})
            assert response.status_code == 422
            assert response.json() == {'detail': 'Cannot identify the image.'}
        # not valid file extension
        with open(self.test_image_dir + 'test.gif','rb') as tmp:
            response = client.post(url,files={'file': tmp})
            assert response.status_code == 422
            assert response.json() == {'detail': 'Image must be between jpg, png, jpeg.'}
        # file cannot grater than 4 Mb
        with open(self.test_image_dir + 'size.png','rb') as tmp:
            response = client.post(url,files={'file': tmp})
            assert response.status_code == 413
            assert response.json() == {'detail':'An image cannot greater than 4 Mb.'}

    @pytest.mark.asyncio
    async def test_upload_image_camera(self,async_client):
        # user login
        response = await async_client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': self.account_1['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = self.prefix + '/upload-image-camera'
        user_id = await self.get_user_id(self.account_1['email'])

        # camera cal is None & planted is False
        with open(self.test_image_dir + 'plant.jpeg','rb') as tmp:
            response = await async_client.post(url,headers={"X-CSRF-TOKEN": csrf_access_token},files={'file': tmp})
            assert response.status_code == 201
            assert response.json() == {"detail": "Successfully upload image."}

            assert 0.0 == await self.get_recent_height(self.account_1['email'])

        # camera cal is True & planted is True
        redis_conn.set(f"camera_cal:{user_id}","true",settings.image_cal_expires)
        await self.set_planted_to_true_false(self.account_1['email'],True)

        with open(self.test_image_dir + 'plant.jpeg','rb') as tmp:
            response = await async_client.post(url,headers={"X-CSRF-TOKEN": csrf_access_token},files={'file': tmp})
            assert response.status_code == 201
            assert response.json() == {"detail": "Successfully upload image."}

            assert 0.0 == await self.get_recent_height(self.account_1['email'])

        # camera cal is False & planted is True
        redis_conn.set(f"camera_cal:{user_id}","false",settings.image_cal_expires)

        with open(self.test_image_dir + 'plant.jpeg','rb') as tmp:
            response = await async_client.post(url,headers={"X-CSRF-TOKEN": csrf_access_token},files={'file': tmp})
            assert response.status_code == 201
            assert response.json() == {"detail": "Successfully upload image."}

            assert 0.0 != await self.get_recent_height(self.account_1['email'])

        # camera cal is None & planted is True
        redis_conn.delete(f"camera_cal:{user_id}")

        with open(self.test_image_dir + 'plant.jpeg','rb') as tmp:
            response = await async_client.post(url,headers={"X-CSRF-TOKEN": csrf_access_token},files={'file': tmp})
            assert response.status_code == 201
            assert response.json() == {"detail": "Successfully upload image."}

            assert 0.0 != await self.get_recent_height(self.account_1['email'])

    def test_recent_plant_image(self,client):
        url = self.prefix + '/recent-plant-image'

        # user login
        client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': self.account_1['password']
        })

        response = client.get(url)
        assert response.status_code == 200
        assert 'image' in response.json()

    @pytest.mark.asyncio
    async def test_delete_plant(self,async_client):
        response = await async_client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': self.account_1['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = '/plants/delete/'
        # delete plant one
        plant_id = await self.get_plant_id(self.name)
        image = await self.get_plant_image(self.name)

        response = await async_client.delete(url + str(plant_id),headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 200
        assert response.json() == {"detail": "Successfully delete the plant."}
        # check image has been delete in directory
        assert Path(self.plant_dir + image).is_file() is False

    @pytest.mark.asyncio
    async def test_delete_user_from_db(self,async_client):
        user_id = await self.get_user_id(self.account_1['email'])
        # delete folder in growth plant
        MagicImage.delete_folder(name_folder=str(user_id),path_delete='camera_module/')
        MagicImage.delete_folder(name_folder=str(user_id),path_delete='camera_module_output/')

        await self.delete_user_from_db()
