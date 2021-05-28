import pytest
from pathlib import Path
from .operationtest import OperationTest
from config import redis_conn
from datetime import datetime, timedelta
from pytz import timezone
from config import settings

tz = timezone(settings.timezone)

class TestSettingUser(OperationTest):
    prefix = "/setting-users"
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
                    'growth_value': '10',
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

    def test_validation_create_setting_user(self,client):
        url = self.prefix + '/create'

        # field required
        response = client.post(url,json={})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'camera': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'token': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'plant_id': assert x['msg'] == 'field required'

        # all field blank
        response = client.post(url,json={'camera': ' ', 'token': ' ', 'plant_id': ' '})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'token': assert x['msg'] == 'ensure this value has at least 5 characters'
            if x['loc'][-1] == 'plant_id': assert x['msg'] == 'ensure this value has at least 1 characters'

        # check all field type data
        response = client.post(url,json={'camera': 'true','token': 123, 'plant_id': 123})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'camera': assert x['msg'] == 'value is not a valid boolean'
            if x['loc'][-1] == 'token': assert x['msg'] == 'str type expected'
            if x['loc'][-1] == 'plant_id': assert x['msg'] == 'str type expected'

    @pytest.mark.asyncio
    async def test_create_setting_user(self,async_client):
        # user login
        response = await async_client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': self.account_1['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = self.prefix + '/create'
        plant_id = await self.get_plant_id(self.name)

        # Plants not found
        response = await async_client.post(url,headers={"X-CSRF-TOKEN": csrf_access_token},json={
            'camera': True,
            'token': 'asdasd',
            'plant_id': '9' * 8
        })
        assert response.status_code == 404
        assert response.json() == {"detail": "Plants not found!"}

        # invalid token
        response = await async_client.post(url,headers={"X-CSRF-TOKEN": csrf_access_token},json={
            'camera': True,
            'token': 'asdasd',
            'plant_id': str(plant_id)
        })
        assert response.status_code == 422
        assert response.json() == {"detail": "Not enough segments"}

        response = await async_client.post(url,headers={"X-CSRF-TOKEN": csrf_access_token},json={
            'camera': True,
            'token': self.iot_token,
            'plant_id': str(plant_id)
        })
        assert response.status_code == 201
        assert response.json() == {"detail": "Successfully create an setting."}

        # user already had setting
        response = await async_client.post(url,headers={"X-CSRF-TOKEN": csrf_access_token},json={
            'camera': True,
            'token': self.iot_token,
            'plant_id': str(plant_id)
        })
        assert response.status_code == 400
        assert response.json() == {"detail": "User already had setting."}

    @pytest.mark.asyncio
    async def test_progress_plant(self,async_client):
        # user login
        response = await async_client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': self.account_1['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = self.prefix + '/progress-plant'
        plant_id = await self.get_plant_id(self.name)

        # delete setting user
        await self.delete_setting_user(self.account_1['email'])

        # percentage 0
        response = await async_client.get(url)
        assert response.status_code == 200
        assert response.json()['percentage'] == 0

        # recreate setting user
        response = await async_client.post(self.prefix + '/create',headers={"X-CSRF-TOKEN": csrf_access_token},json={
            'camera': True,
            'token': self.iot_token,
            'plant_id': str(plant_id)
        })
        assert response.status_code == 201
        assert response.json() == {"detail": "Successfully create an setting."}

        # percentage 0
        response = await async_client.get(url)
        assert response.status_code == 200
        assert response.json()['percentage'] == 0

        # change planted_at time & planted true
        time_now = datetime.now(tz).replace(tzinfo=None)
        await self.set_planted_at(self.account_1['email'],time_now - timedelta(days=2))
        await self.set_planted_to_true_false(self.account_1['email'],True)

        # percentage != 0
        response = await async_client.get(url)
        assert response.status_code == 200
        assert response.json()['percentage'] == 20

    def test_my_setting(self,client):
        url = self.prefix + '/my-setting'

        # user login
        client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': self.account_1['password']
        })

        response = client.get(url)
        assert response.status_code == 200
        assert 'setting_users_id' in response.json()
        assert 'setting_users_camera' in response.json()
        assert 'setting_users_control_type' in response.json()
        assert 'setting_users_token' in response.json()
        assert 'setting_users_ph_max' in response.json()
        assert 'setting_users_ph_min' in response.json()
        assert 'setting_users_tds_min' in response.json()
        assert 'setting_users_ph_cal' in response.json()
        assert 'setting_users_tds_cal' in response.json()
        assert 'setting_users_tank_height' in response.json()
        assert 'setting_users_tank_min' in response.json()
        assert 'setting_users_servo_horizontal' in response.json()
        assert 'setting_users_servo_vertical' in response.json()
        assert 'setting_users_planted' in response.json()
        assert 'setting_users_created_at' in response.json()
        assert 'setting_users_planted_at' in response.json()
        assert 'plants_id' in response.json()
        assert 'plants_ph_max' in response.json()
        assert 'plants_ph_min' in response.json()
        assert 'plants_tds_min' in response.json()

    @pytest.mark.asyncio
    async def test_change_setting_camera(self,async_client):
        # user login
        response = await async_client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': self.account_1['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = self.prefix + '/change-camera'
        plant_id = await self.get_plant_id(self.name)

        # delete setting user
        await self.delete_setting_user(self.account_1['email'])

        # setting not found
        response = await async_client.put(url,headers={"X-CSRF-TOKEN": csrf_access_token})
        assert response.status_code == 404
        assert response.json() == {"detail": "Setting not found!"}

        # recreate setting user
        response = await async_client.post(self.prefix + '/create',headers={"X-CSRF-TOKEN": csrf_access_token},json={
            'camera': True,
            'token': self.iot_token,
            'plant_id': str(plant_id)
        })
        assert response.status_code == 201
        assert response.json() == {"detail": "Successfully create an setting."}

        response = await async_client.put(url,headers={"X-CSRF-TOKEN": csrf_access_token})
        assert response.status_code == 200
        assert response.json() == {"detail": "Successfully change the camera to False."}

        response = await async_client.put(url,headers={"X-CSRF-TOKEN": csrf_access_token})
        assert response.status_code == 200
        assert response.json() == {"detail": "Successfully change the camera to True."}

    @pytest.mark.asyncio
    async def test_change_setting_control_type(self,async_client):
        # user login
        response = await async_client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': self.account_1['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = self.prefix + '/change-control-type'
        plant_id = await self.get_plant_id(self.name)

        # delete setting user
        await self.delete_setting_user(self.account_1['email'])

        # setting not found
        response = await async_client.put(url,headers={"X-CSRF-TOKEN": csrf_access_token})
        assert response.status_code == 404
        assert response.json() == {"detail": "Setting not found!"}

        # recreate setting user
        response = await async_client.post(self.prefix + '/create',headers={"X-CSRF-TOKEN": csrf_access_token},json={
            'camera': True,
            'token': self.iot_token,
            'plant_id': str(plant_id)
        })
        assert response.status_code == 201
        assert response.json() == {"detail": "Successfully create an setting."}

        response = await async_client.put(url,headers={"X-CSRF-TOKEN": csrf_access_token})
        assert response.status_code == 200
        assert response.json() == {"detail": "Successfully change the control type to False."}

        response = await async_client.put(url,headers={"X-CSRF-TOKEN": csrf_access_token})
        assert response.status_code == 200
        assert response.json() == {"detail": "Successfully change the control type to True."}

    def test_validation_change_setting_token(self,client):
        url = self.prefix + '/change-token'

        # field required
        response = client.put(url,json={})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'token': assert x['msg'] == 'field required'

        # all field blank
        response = client.put(url,json={'token': ' '})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'token': assert x['msg'] == 'ensure this value has at least 5 characters'

        # check all field type data
        response = client.put(url,json={'token': 123})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'token': assert x['msg'] == 'str type expected'

    @pytest.mark.asyncio
    async def test_change_setting_token(self,async_client,authorize):
        # user login
        response = await async_client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': self.account_1['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = self.prefix + '/change-token'
        plant_id = await self.get_plant_id(self.name)

        # delete setting user
        await self.delete_setting_user(self.account_1['email'])

        # setting not found
        response = await async_client.put(url,headers={"X-CSRF-TOKEN": csrf_access_token},json={'token': 'asdasd'})
        assert response.status_code == 404
        assert response.json() == {"detail": "Setting not found!"}

        # recreate setting user
        response = await async_client.post(self.prefix + '/create',headers={"X-CSRF-TOKEN": csrf_access_token},json={
            'camera': True,
            'token': self.iot_token,
            'plant_id': str(plant_id)
        })
        assert response.status_code == 201
        assert response.json() == {"detail": "Successfully create an setting."}

        # invalid token
        response = await async_client.put(url,headers={"X-CSRF-TOKEN": csrf_access_token},json={'token': 'asdasd'})
        assert response.status_code == 422
        assert response.json() == {"detail": "Not enough segments"}

        response = await async_client.put(url,headers={"X-CSRF-TOKEN": csrf_access_token},json={'token': self.iot_token})
        assert response.status_code == 200
        assert response.json() == {"detail": "Successfully change the user token."}

        # check token has been revoked in redis
        jti = authorize.get_raw_jwt(self.iot_token)['jti']
        assert redis_conn.get(jti) == 'true'

    def test_validation_change_settings(self,client):
        url = self.prefix + '/change-settings'

        # field required
        response = client.put(url,json={})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'ph_max': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'ph_min': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'tds_min': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'ph_cal': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'tds_cal': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'tank_height': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'tank_min': assert x['msg'] == 'field required'

        # all field blank
        response = client.put(url,json={
            'ph_max': -1,
            'ph_min': -1,
            'tds_min': -1,
            'ph_cal': -1,
            'tds_cal': -1,
            'tank_height': -1,
            'tank_min': -1
        })
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'ph_max': assert x['msg'] == 'ensure this value is greater than or equal to 0'
            if x['loc'][-1] == 'ph_min': assert x['msg'] == 'ensure this value is greater than or equal to 0'
            if x['loc'][-1] == 'tds_min': assert x['msg'] == 'ensure this value is greater than or equal to 0'
            if x['loc'][-1] == 'ph_cal': assert x['msg'] == 'ensure this value is greater than or equal to 0'
            if x['loc'][-1] == 'tds_cal': assert x['msg'] == 'ensure this value is greater than or equal to 0'
            if x['loc'][-1] == 'tank_height': assert x['msg'] == 'ensure this value is greater than or equal to 0'
            if x['loc'][-1] == 'tank_min': assert x['msg'] == 'ensure this value is greater than or equal to 0'

        # test limit value
        response = client.put(url,json={
            'ph_max': 10000000,
            'ph_min': 10000000,
            'tds_min': 10000000,
            'ph_cal': 10000000,
            'tds_cal': 10000000,
            'tank_height': 10000000,
            'tank_min': 10000000
        })
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'ph_max': assert x['msg'] == 'ensure this value is less than or equal to 20'
            if x['loc'][-1] == 'ph_min': assert x['msg'] == 'ensure this value is less than or equal to 20'
            if x['loc'][-1] == 'tds_min': assert x['msg'] == 'ensure this value is less than or equal to 3000'
            if x['loc'][-1] == 'ph_cal': assert x['msg'] == 'ensure this value is less than or equal to 10000'
            if x['loc'][-1] == 'tds_cal': assert x['msg'] == 'ensure this value is less than or equal to 10000'
            if x['loc'][-1] == 'tank_height': assert x['msg'] == 'ensure this value is less than or equal to 1000000'
            if x['loc'][-1] == 'tank_min': assert x['msg'] == 'ensure this value is less than or equal to 1000000'

        # check all field type data
        response = client.put(url,json={
            'ph_max': 'asd',
            'ph_min': 'asd',
            'tds_min': 'asd',
            'ph_cal': 'asd',
            'tds_cal': 'asd',
            'tank_height': 'asd',
            'tank_min': 'asd'
        })
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'ph_max': assert x['msg'] == 'value is not a valid float'
            if x['loc'][-1] == 'ph_min': assert x['msg'] == 'value is not a valid float'
            if x['loc'][-1] == 'tds_min': assert x['msg'] == 'value is not a valid float'
            if x['loc'][-1] == 'ph_cal': assert x['msg'] == 'value is not a valid float'
            if x['loc'][-1] == 'tds_cal': assert x['msg'] == 'value is not a valid float'
            if x['loc'][-1] == 'tank_height': assert x['msg'] == 'value is not a valid integer'
            if x['loc'][-1] == 'tank_min': assert x['msg'] == 'value is not a valid integer'

    @pytest.mark.asyncio
    async def test_change_settings(self,async_client):
        # user login
        response = await async_client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': self.account_1['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = self.prefix + '/change-settings'
        plant_id = await self.get_plant_id(self.name)

        # delete setting user
        await self.delete_setting_user(self.account_1['email'])

        # setting not found
        response = await async_client.put(url,headers={"X-CSRF-TOKEN": csrf_access_token},json={
            'ph_max': 0,
            'ph_min': 0,
            'tds_min': 0,
            'ph_cal': 0,
            'tds_cal': 0,
            'tank_height': 0,
            'tank_min': 0
        })
        assert response.status_code == 404
        assert response.json() == {"detail": "Setting not found!"}

        # recreate setting user
        response = await async_client.post(self.prefix + '/create',headers={"X-CSRF-TOKEN": csrf_access_token},json={
            'camera': True,
            'token': self.iot_token,
            'plant_id': str(plant_id)
        })
        assert response.status_code == 201
        assert response.json() == {"detail": "Successfully create an setting."}

        response = await async_client.put(url,headers={"X-CSRF-TOKEN": csrf_access_token},json={
            'ph_max': 1,
            'ph_min': 1,
            'tds_min': 1,
            'ph_cal': 1,
            'tds_cal': 1,
            'tank_height': 1,
            'tank_min': 1
        })
        assert response.status_code == 200
        assert response.json() == {"detail": "Successfully update the control setting."}

    def test_validation_change_servo(self,client):
        url = self.prefix + '/change-servo'

        # field required
        response = client.put(url,json={})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'servo_horizontal': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'servo_vertical': assert x['msg'] == 'field required'

        # all field blank
        response = client.put(url,json={'servo_horizontal': -1, 'servo_vertical': -1})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'servo_horizontal': assert x['msg'] == 'ensure this value is greater than or equal to 0'
            if x['loc'][-1] == 'servo_vertical': assert x['msg'] == 'ensure this value is greater than or equal to 0'

        # test limit value
        response = client.put(url,json={'servo_horizontal': 181, 'servo_vertical': 181})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'servo_horizontal': assert x['msg'] == 'ensure this value is less than or equal to 180'
            if x['loc'][-1] == 'servo_vertical': assert x['msg'] == 'ensure this value is less than or equal to 180'

        # check all field type data
        response = client.put(url,json={'servo_horizontal': 'asd', 'servo_vertical': 'asd'})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'servo_horizontal': assert x['msg'] == 'value is not a valid integer'
            if x['loc'][-1] == 'servo_vertical': assert x['msg'] == 'value is not a valid integer'

    @pytest.mark.asyncio
    async def test_change_servo(self,async_client):
        # user login
        response = await async_client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': self.account_1['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = self.prefix + '/change-servo'
        plant_id = await self.get_plant_id(self.name)

        # delete setting user
        await self.delete_setting_user(self.account_1['email'])

        # setting not found
        response = await async_client.put(url,headers={"X-CSRF-TOKEN": csrf_access_token},json={
            'servo_horizontal': 0,
            'servo_vertical': 0,
        })
        assert response.status_code == 404
        assert response.json() == {"detail": "Setting not found!"}

        # recreate setting user
        response = await async_client.post(self.prefix + '/create',headers={"X-CSRF-TOKEN": csrf_access_token},json={
            'camera': True,
            'token': self.iot_token,
            'plant_id': str(plant_id)
        })
        assert response.status_code == 201
        assert response.json() == {"detail": "Successfully create an setting."}

        response = await async_client.put(url,headers={"X-CSRF-TOKEN": csrf_access_token},json={
            'servo_horizontal': 1,
            'servo_vertical': 1
        })
        assert response.status_code == 200
        assert response.json() == {"detail": "Successfully update the servo setting."}

    def test_validation_change_setting_plants(self,client):
        url = self.prefix + '/change-plants/'

        # all field blank
        response = client.put(url + '0')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'plant_id': assert x['msg'] == 'ensure this value is greater than 0'
        # check all field type data
        response = client.put(url + 'a')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'plant_id': assert x['msg'] == 'value is not a valid integer'

    @pytest.mark.asyncio
    async def test_change_setting_plants(self,async_client):
        # user login
        response = await async_client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': self.account_1['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = self.prefix + '/change-plants/'
        plant_id = await self.get_plant_id(self.name)

        # delete setting user
        await self.delete_setting_user(self.account_1['email'])

        # setting not found
        response = await async_client.put(url + str(plant_id),headers={"X-CSRF-TOKEN": csrf_access_token})
        assert response.status_code == 404
        assert response.json() == {"detail": "Setting not found!"}

        # recreate setting user
        response = await async_client.post(self.prefix + '/create',headers={"X-CSRF-TOKEN": csrf_access_token},json={
            'camera': True,
            'token': self.iot_token,
            'plant_id': str(plant_id)
        })
        assert response.status_code == 201
        assert response.json() == {"detail": "Successfully create an setting."}

        # Plants not found
        response = await async_client.put(url + '9' * 8,headers={"X-CSRF-TOKEN": csrf_access_token})
        assert response.status_code == 404
        assert response.json() == {"detail": "Plants not found!"}

        # set planted to true
        await self.set_planted_to_true_false(self.account_1['email'],True)
        # other plants still ongoing
        response = await async_client.put(url + str(plant_id),headers={"X-CSRF-TOKEN": csrf_access_token})
        assert response.status_code == 400
        assert response.json() == {"detail": "Upss, you have other plants still ongoing."}
        # set planted to false
        await self.set_planted_to_true_false(self.account_1['email'],False)

        response = await async_client.put(url + str(plant_id),headers={"X-CSRF-TOKEN": csrf_access_token})
        assert response.status_code == 200
        assert response.json() == {"detail": "Successfully change the user plants."}

    @pytest.mark.asyncio
    async def test_change_setting_plants_status(self,async_client):
        # user login
        response = await async_client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': self.account_1['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = self.prefix + '/change-plants-status'
        plant_id = await self.get_plant_id(self.name)

        # delete setting user
        await self.delete_setting_user(self.account_1['email'])

        # setting not found
        response = await async_client.put(url,headers={"X-CSRF-TOKEN": csrf_access_token})
        assert response.status_code == 404
        assert response.json() == {"detail": "Setting not found!"}

        # recreate setting user
        response = await async_client.post(self.prefix + '/create',headers={"X-CSRF-TOKEN": csrf_access_token},json={
            'camera': True,
            'token': self.iot_token,
            'plant_id': str(plant_id)
        })
        assert response.status_code == 201
        assert response.json() == {"detail": "Successfully create an setting."}

        response = await async_client.put(url,headers={"X-CSRF-TOKEN": csrf_access_token})
        assert response.status_code == 200
        assert response.json() == {"detail": "Successfully change the planted to True."}

        response = await async_client.put(url,headers={"X-CSRF-TOKEN": csrf_access_token})
        assert response.status_code == 200
        assert response.json() == {"detail": "Successfully change the planted to False."}

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
        await self.delete_user_from_db()
