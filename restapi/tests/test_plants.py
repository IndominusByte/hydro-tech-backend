import pytest
from pathlib import Path
from .operationtest import OperationTest

class TestPlant(OperationTest):
    prefix = "/plants"

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

    def test_validation_create_plant(self,client):
        url = self.prefix + '/create'

        # field required
        response = client.post(url,data={})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'image': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'name': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'desc': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'ph_max': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'ph_min': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'tds_min': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'growth_value': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'growth_type': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'difficulty_level': assert x['msg'] == 'field required'

        # all field blank
        response = client.post(url,data={
            'name': ' ',
            'desc': ' ',
            'ph_max': 0.0,
            'ph_min': 0.0,
            'tds_min': 0.0,
            'growth_value': 0,
            'growth_type': ' ',
            'difficulty_level': ' '
        })
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'name': assert x['msg'] == 'ensure this value has at least 3 characters'
            if x['loc'][-1] == 'desc': assert x['msg'] == 'ensure this value has at least 20 characters'
            if x['loc'][-1] == 'ph_max': assert x['msg'] == 'ensure this value is greater than 0'
            if x['loc'][-1] == 'ph_min': assert x['msg'] == 'ensure this value is greater than 0'
            if x['loc'][-1] == 'tds_min': assert x['msg'] == 'ensure this value is greater than 0'
            if x['loc'][-1] == 'growth_value': assert x['msg'] == 'ensure this value is greater than 0'

        # test limit value
        response = client.post(url,data={
            'name': 'a' * 200,
            'desc': 'a' * 200,
            'ph_max': 4000,
            'ph_min': 4000,
            'tds_min': 4000,
            'growth_value': 4000
        })
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'name': assert x['msg'] == 'ensure this value has at most 100 characters'
            if x['loc'][-1] == 'ph_max': assert x['msg'] == 'ensure this value is less than or equal to 20'
            if x['loc'][-1] == 'ph_min': assert x['msg'] == 'ensure this value is less than or equal to 20'
            if x['loc'][-1] == 'tds_min': assert x['msg'] == 'ensure this value is less than or equal to 3000'

        # check all field type data
        response = client.post(url,data={
            'name': 123,
            'desc': 123,
            'ph_max': 'asd',
            'ph_min': 'asd',
            'tds_min': 'asd',
            'growth_value': 'asd',
            'growth_type': 1,
            'difficulty_level': 1
        })
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'ph_max': assert x['msg'] == 'value is not a valid float'
            if x['loc'][-1] == 'ph_min': assert x['msg'] == 'value is not a valid float'
            if x['loc'][-1] == 'tds_min': assert x['msg'] == 'value is not a valid float'
            if x['loc'][-1] == 'growth_value': assert x['msg'] == 'value is not a valid integer'
            if x['loc'][-1] == 'growth_type': assert x['msg'] == "unexpected value; permitted: 'days', 'weeks'"
            if x['loc'][-1] == 'difficulty_level': assert x['msg'] == "unexpected value; permitted: 'easy', 'medium', 'hard'"

        # danger file extension
        with open(self.test_image_dir + 'test.txt','rb') as tmp:
            response = client.post(url,files={'image': tmp})
            assert response.status_code == 422
            assert response.json() == {'detail': 'Cannot identify the image.'}
        # not valid file extension
        with open(self.test_image_dir + 'test.gif','rb') as tmp:
            response = client.post(url,files={'image': tmp})
            assert response.status_code == 422
            assert response.json() == {'detail': 'Image must be between jpg, png, jpeg.'}
        # file cannot grater than 4 Mb
        with open(self.test_image_dir + 'size.png','rb') as tmp:
            response = client.post(url,files={'image': tmp})
            assert response.status_code == 413
            assert response.json() == {'detail':'An image cannot greater than 4 Mb.'}

    @pytest.mark.asyncio
    async def test_create_plant(self,async_client):
        response = await async_client.post('/users/login',json={
            'email': self.account_2['email'],
            'password': self.account_2['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = self.prefix + '/create'

        # check user is admin
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
            assert response.status_code == 401
            assert response.json() == {"detail": "Only users with admin privileges can do this action."}

        # user admin login
        response = await async_client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': self.account_1['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

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

    def test_name_duplicate_create_plant(self,client):
        response = client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': self.account_1['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = self.prefix + '/create'

        with open(self.test_image_dir + 'image.jpeg','rb') as tmp:
            response = client.post(url,
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
            assert response.status_code == 400
            assert response.json() == {"detail": "The name has already been taken."}

    def test_validation_get_all_plants(self,client):
        url = self.prefix + '/all-plants'
        # field required
        response = client.get(url)
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'page': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'per_page': assert x['msg'] == 'field required'

        # all field blank
        response = client.get(url + '?page=0&per_page=0&q=&difficulty=')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'page': assert x['msg'] == 'ensure this value is greater than 0'
            if x['loc'][-1] == 'per_page': assert x['msg'] == 'ensure this value is greater than 0'
            if x['loc'][-1] == 'q': assert x['msg'] == 'ensure this value has at least 1 characters'

        # check all field type data
        response = client.get(url + '?page=a&per_page=a&q=123&difficulty=123')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'page': assert x['msg'] == 'value is not a valid integer'
            if x['loc'][-1] == 'per_page': assert x['msg'] == 'value is not a valid integer'
            if x['loc'][-1] == 'difficulty': assert x['msg'] == "unexpected value; permitted: 'easy', 'medium', 'hard'"

    def test_get_all_plants(self,client):
        url = self.prefix + '/all-plants'

        response = client.get(url + '?page=1&per_page=1')
        assert response.status_code == 200
        assert 'data' in response.json()
        assert 'total' in response.json()
        assert 'next_num' in response.json()
        assert 'prev_num' in response.json()
        assert 'page' in response.json()
        assert 'iter_pages' in response.json()

        # check data exists and type data
        assert type(response.json()['data'][0]['plants_id']) == str
        assert type(response.json()['data'][0]['plants_name']) == str
        assert type(response.json()['data'][0]['plants_image']) == str
        assert type(response.json()['data'][0]['plants_desc']) == str
        assert type(response.json()['data'][0]['plants_ph_min']) == float
        assert type(response.json()['data'][0]['plants_ph_max']) == float
        assert type(response.json()['data'][0]['plants_tds_min']) == float
        assert type(response.json()['data'][0]['plants_growth_value']) == int
        assert type(response.json()['data'][0]['plants_growth_type']) == str
        assert type(response.json()['data'][0]['plants_difficulty_level']) == str
        assert type(response.json()['data'][0]['plants_created_at']) == str
        assert type(response.json()['data'][0]['plants_updated_at']) == str

    def test_validation_get_plant_by_id(self,client):
        url = self.prefix + '/get-plant/'
        # all field blank
        response = client.get(url + '0')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'plant_id': assert x['msg'] == 'ensure this value is greater than 0'
        # check all field type data
        response = client.get(url + 'a')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'plant_id': assert x['msg'] == 'value is not a valid integer'

    @pytest.mark.asyncio
    async def test_get_plant_by_id(self,async_client):
        url = self.prefix + '/get-plant/'
        plant_id = await self.get_plant_id(self.name)

        # Plants not found
        response = await async_client.get(url + '9' * 8)
        assert response.status_code == 404
        assert response.json() == {"detail": "Plants not found!"}

        response = await async_client.get(url + str(plant_id))
        assert response.status_code == 200
        assert "plants_id" in response.json()
        assert "plants_name" in response.json()
        assert "plants_image" in response.json()
        assert "plants_desc" in response.json()
        assert "plants_ph_min" in response.json()
        assert "plants_ph_max" in response.json()
        assert "plants_tds_min" in response.json()
        assert "plants_growth_value" in response.json()
        assert "plants_growth_type" in response.json()
        assert "plants_difficulty_level" in response.json()
        assert "plants_created_at" in response.json()
        assert "plants_updated_at" in response.json()

    def test_validation_update_plant(self,client):
        url = self.prefix + '/update/'

        # field required
        response = client.put(url + '0',data={})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'image': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'name': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'desc': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'ph_max': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'ph_min': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'tds_min': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'growth_value': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'growth_type': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'difficulty_level': assert x['msg'] == 'field required'

        # all field blank
        response = client.put(url + '0',data={
            'name': ' ',
            'desc': ' ',
            'ph_max': 0.0,
            'ph_min': 0.0,
            'tds_min': 0.0,
            'growth_value': 0,
            'growth_type': ' ',
            'difficulty_level': ' '
        })
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'plant_id': assert x['msg'] == 'ensure this value is greater than 0'
            if x['loc'][-1] == 'name': assert x['msg'] == 'ensure this value has at least 3 characters'
            if x['loc'][-1] == 'desc': assert x['msg'] == 'ensure this value has at least 20 characters'
            if x['loc'][-1] == 'ph_max': assert x['msg'] == 'ensure this value is greater than 0'
            if x['loc'][-1] == 'ph_min': assert x['msg'] == 'ensure this value is greater than 0'
            if x['loc'][-1] == 'tds_min': assert x['msg'] == 'ensure this value is greater than 0'
            if x['loc'][-1] == 'growth_value': assert x['msg'] == 'ensure this value is greater than 0'

        # test limit value
        response = client.put(url + '1',data={
            'name': 'a' * 200,
            'desc': 'a' * 200,
            'ph_max': 4000,
            'ph_min': 4000,
            'tds_min': 4000,
            'growth_value': 4000
        })
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'name': assert x['msg'] == 'ensure this value has at most 100 characters'
            if x['loc'][-1] == 'ph_max': assert x['msg'] == 'ensure this value is less than or equal to 20'
            if x['loc'][-1] == 'ph_min': assert x['msg'] == 'ensure this value is less than or equal to 20'
            if x['loc'][-1] == 'tds_min': assert x['msg'] == 'ensure this value is less than or equal to 3000'

        # check all field type data
        response = client.put(url + 'a',data={
            'name': 123,
            'desc': 123,
            'ph_max': 'asd',
            'ph_min': 'asd',
            'tds_min': 'asd',
            'growth_value': 'asd',
            'growth_type': 1,
            'difficulty_level': 1
        })
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'plant_id': assert x['msg'] == 'value is not a valid integer'
            if x['loc'][-1] == 'ph_max': assert x['msg'] == 'value is not a valid float'
            if x['loc'][-1] == 'ph_min': assert x['msg'] == 'value is not a valid float'
            if x['loc'][-1] == 'tds_min': assert x['msg'] == 'value is not a valid float'
            if x['loc'][-1] == 'growth_value': assert x['msg'] == 'value is not a valid integer'
            if x['loc'][-1] == 'growth_type': assert x['msg'] == "unexpected value; permitted: 'days', 'weeks'"
            if x['loc'][-1] == 'difficulty_level': assert x['msg'] == "unexpected value; permitted: 'easy', 'medium', 'hard'"

        # danger file extension
        with open(self.test_image_dir + 'test.txt','rb') as tmp:
            response = client.put(url + '1',files={'image': tmp})
            assert response.status_code == 422
            assert response.json() == {'detail': 'Cannot identify the image.'}
        # not valid file extension
        with open(self.test_image_dir + 'test.gif','rb') as tmp:
            response = client.put(url + '1',files={'image': tmp})
            assert response.status_code == 422
            assert response.json() == {'detail': 'Image must be between jpg, png, jpeg.'}
        # file cannot grater than 4 Mb
        with open(self.test_image_dir + 'size.png','rb') as tmp:
            response = client.put(url + '1',files={'image': tmp})
            assert response.status_code == 413
            assert response.json() == {'detail':'An image cannot greater than 4 Mb.'}

    @pytest.mark.asyncio
    async def test_update_plant(self,async_client):
        response = await async_client.post('/users/login',json={
            'email': self.account_2['email'],
            'password': self.account_2['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = self.prefix + '/update/'
        plant_id = await self.get_plant_id(self.name)

        # check user is admin
        response = await async_client.put(url + str(plant_id),
            headers={'X-CSRF-TOKEN': csrf_access_token},
            data={'name': self.name,
                'desc': 'b' * 30,
                'ph_max': '2.0',
                'ph_min': '2.0',
                'tds_min': '2.0',
                'growth_value': '2',
                'growth_type': 'weeks',
                'difficulty_level': 'medium'}
        )
        assert response.status_code == 401
        assert response.json() == {"detail": "Only users with admin privileges can do this action."}

        # user admin login
        response = await async_client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': self.account_1['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        # Plants not found
        response = await async_client.put(url + '9' * 8,
            headers={'X-CSRF-TOKEN': csrf_access_token},
            data={'name': self.name,
                'desc': 'b' * 30,
                'ph_max': '2.0',
                'ph_min': '2.0',
                'tds_min': '2.0',
                'growth_value': '2',
                'growth_type': 'weeks',
                'difficulty_level': 'medium'}
        )
        assert response.status_code == 404
        assert response.json() == {"detail": "Plants not found!"}

        image = await self.get_plant_image(self.name)

        with open(self.test_image_dir + 'image.jpeg','rb') as tmp:
            response = await async_client.put(url + str(plant_id),
                headers={'X-CSRF-TOKEN': csrf_access_token},
                data={'name': self.name,
                    'desc': 'b' * 30,
                    'ph_max': '2.0',
                    'ph_min': '2.0',
                    'tds_min': '2.0',
                    'growth_value': '2',
                    'growth_type': 'weeks',
                    'difficulty_level': 'medium'},
                files={'image': tmp}
            )
            assert response.status_code == 200
            assert response.json() == {"detail": "Successfully update the plant."}

        # check the previous image doesn't exists in directory
        assert Path(self.plant_dir + image).is_file() is False

    @pytest.mark.asyncio
    async def test_name_duplicate_update_plant(self,async_client):
        # user admin login
        response = await async_client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': self.account_1['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = self.prefix + '/create'

        # create another plant
        with open(self.test_image_dir + 'image.jpeg','rb') as tmp:
            response = await async_client.post(url,
                data={
                    'name': self.name2,
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

        url = self.prefix + '/update/'
        plant_id = await self.get_plant_id(self.name2)

        # name already taken
        with open(self.test_image_dir + 'image.jpeg','rb') as tmp:
            response = await async_client.put(url + str(plant_id),
                headers={'X-CSRF-TOKEN': csrf_access_token},
                data={'name': self.name,
                    'desc': 'b' * 30,
                    'ph_max': '2.0',
                    'ph_min': '2.0',
                    'tds_min': '2.0',
                    'growth_value': '2',
                    'growth_type': 'weeks',
                    'difficulty_level': 'medium'},
                files={'image': tmp}
            )
            assert response.status_code == 400
            assert response.json() == {"detail": "The name has already been taken."}

    def test_validation_delete_plant(self,client):
        url = self.prefix + '/delete/'
        # all field blank
        response = client.delete(url + '0')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'plant_id': assert x['msg'] == 'ensure this value is greater than 0'
        # check all field type data
        response = client.delete(url + 'a')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'plant_id': assert x['msg'] == 'value is not a valid integer'

    @pytest.mark.asyncio
    async def test_delete_plant(self,async_client):
        response = await async_client.post('/users/login',json={
            'email': self.account_2['email'],
            'password': self.account_2['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = self.prefix + '/delete/'

        plant_id = await self.get_plant_id(self.name)
        image = await self.get_plant_image(self.name)

        # check user is admin
        response = await async_client.delete(url + str(plant_id),headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 401
        assert response.json() == {"detail": "Only users with admin privileges can do this action."}

        # user admin login
        response = await async_client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': self.account_1['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')
        # Plants not found
        response = await async_client.delete(url + '9' * 8,headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 404
        assert response.json() == {"detail": "Plants not found!"}

        # delete plant one
        response = await async_client.delete(url + str(plant_id),headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 200
        assert response.json() == {"detail": "Successfully delete the plant."}
        # check image has been delete in directory
        assert Path(self.plant_dir + image).is_file() is False

        # delete plant two
        plant_id = await self.get_plant_id(self.name2)
        image = await self.get_plant_image(self.name2)

        response = await async_client.delete(url + str(plant_id),headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 200
        assert response.json() == {"detail": "Successfully delete the plant."}
        # check image has been delete in directory
        assert Path(self.plant_dir + image).is_file() is False

    @pytest.mark.asyncio
    async def test_delete_user_from_db(self,async_client):
        await self.delete_user_from_db()
