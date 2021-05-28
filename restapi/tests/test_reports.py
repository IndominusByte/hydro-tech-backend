import pytest
from pathlib import Path
from .operationtest import OperationTest

class TestReport(OperationTest):
    prefix = "/reports"
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

    @pytest.mark.asyncio
    async def test_create_report(self,async_client):
        await self.create_report(self.account_1['email'])

    def test_validation_get_all_reports(self,client):
        url = self.prefix + '/all-reports'
        # field required
        response = client.get(url)
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'order_by': assert x['msg'] == 'field required'

        # check all field type data
        response = client.get(url + '?order_by=')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'order_by': assert x['msg'] == \
                "unexpected value; permitted: 'today', '7day', '30day', '90day'"

    def test_get_all_reports(self,client):
        client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': self.account_1['password']
        })

        url = self.prefix + '/all-reports'

        response = client.get(url + '?order_by=today')
        assert response.status_code == 200
        assert len(response.json()) == 1

        # check data exists and type data
        assert type(response.json()[0]['id']) == str
        assert type(response.json()[0]['ph']) == float
        assert type(response.json()[0]['tds']) == float
        assert type(response.json()[0]['temp']) == float
        assert type(response.json()[0]['ldr']) == str
        assert type(response.json()[0]['tank']) == int
        assert type(response.json()[0]['created_at']) == str

    def test_validation_ph_chart_report(self,client):
        url = self.prefix + '/ph-chart-report'
        # field required
        response = client.get(url)
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'order_by': assert x['msg'] == 'field required'

        # check all field type data
        response = client.get(url + '?order_by=')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'order_by': assert x['msg'] == \
                "unexpected value; permitted: '7day', '30day'"

    def test_ph_chart_report(self,client):
        client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': self.account_1['password']
        })

        url = self.prefix + '/ph-chart-report'

        response = client.get(url + '?order_by=7day')
        assert response.status_code == 200
        assert len(response.json()) == 7

        response = client.get(url + '?order_by=30day')
        assert response.status_code == 200
        assert len(response.json()) == 4

        # check data exists and type data
        assert type(response.json()[0]['avg']) == float
        assert type(response.json()[0]['date']) == str

    def test_validation_tds_chart_report(self,client):
        url = self.prefix + '/tds-chart-report'
        # field required
        response = client.get(url)
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'order_by': assert x['msg'] == 'field required'

        # check all field type data
        response = client.get(url + '?order_by=')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'order_by': assert x['msg'] == \
                "unexpected value; permitted: '7day', '30day'"

    def test_tds_chart_report(self,client):
        client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': self.account_1['password']
        })

        url = self.prefix + '/tds-chart-report'

        response = client.get(url + '?order_by=7day')
        assert response.status_code == 200
        assert len(response.json()) == 7

        response = client.get(url + '?order_by=30day')
        assert response.status_code == 200
        assert len(response.json()) == 4

        # check data exists and type data
        assert type(response.json()[0]['avg']) == float
        assert type(response.json()[0]['date']) == str

    def test_validation_growth_plant_chart_report(self,client):
        url = self.prefix + '/growth-plant-chart-report'
        # field required
        response = client.get(url)
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'order_by': assert x['msg'] == 'field required'

        # check all field type data
        response = client.get(url + '?order_by=')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'order_by': assert x['msg'] == \
                "unexpected value; permitted: '7day', '30day'"

    def test_growth_plant_chart_report(self,client):
        client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': self.account_1['password']
        })

        url = self.prefix + '/growth-plant-chart-report'

        response = client.get(url + '?order_by=7day')
        assert response.status_code == 200
        assert len(response.json()) == 7

        response = client.get(url + '?order_by=30day')
        assert response.status_code == 200
        assert len(response.json()) == 4

        # check data exists and type data
        assert type(response.json()[0]['avg']) == float
        assert type(response.json()[0]['date']) == str

    def test_validation_alert_report(self,client):
        url = self.prefix + '/alert-report'
        # field required
        response = client.get(url)
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'order_by': assert x['msg'] == 'field required'

        # check all field type data
        response = client.get(url + '?order_by=')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'order_by': assert x['msg'] == \
                "unexpected value; permitted: 'today', '3day', '7day'"

    @pytest.mark.asyncio
    async def test_alert_report(self,async_client):
        # user login
        response = await async_client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': self.account_1['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = self.prefix + '/alert-report'
        plant_id = await self.get_plant_id(self.name)

        # create setting user
        response = await async_client.post('/setting-users/create',headers={"X-CSRF-TOKEN": csrf_access_token},json={
            'camera': True,
            'token': self.iot_token,
            'plant_id': str(plant_id)
        })
        assert response.status_code == 201
        assert response.json() == {"detail": "Successfully create an setting."}

        # setting user planted to True
        response = await async_client.put('/setting-users/change-plants-status',headers={"X-CSRF-TOKEN": csrf_access_token})
        assert response.status_code == 200
        assert response.json() == {"detail": "Successfully change the planted to True."}

        response = await async_client.get(url + '?order_by=today')
        assert response.status_code == 200
        assert len(response.json()) == 1

        # check data exists and type data
        assert type(response.json()[0]['id']) == str
        assert type(response.json()[0]['type']) == str
        assert type(response.json()[0]['message']) == str
        assert type(response.json()[0]['user_id']) == str
        assert type(response.json()[0]['created_at']) == str

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
