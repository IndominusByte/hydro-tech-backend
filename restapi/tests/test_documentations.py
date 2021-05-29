import pytest
from .operationtest import OperationTest

class TestDocumentation(OperationTest):
    prefix = "/documentations"

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

    def test_create_category_doc(self,client):
        response = client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': self.account_1['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = '/category-docs/create'

        response = client.post(url,json={'name': self.name},headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 201
        assert response.json() == {"detail": "Successfully add a new category-doc."}

    def test_validation_create_documentation(self,client):
        url = self.prefix + '/create'

        # field required
        response = client.post(url,json={})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'title': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'description': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'category_doc_id': assert x['msg'] == 'field required'

        # all field blank
        response = client.post(url,json={'title': ' ','description': ' ','category_doc_id': 0})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'title': assert x['msg'] == 'ensure this value has at least 3 characters'
            if x['loc'][-1] == 'description': assert x['msg'] == 'ensure this value has at least 20 characters'
            if x['loc'][-1] == 'category_doc_id': assert x['msg'] == 'ensure this value is greater than 0'

        # test limit value
        response = client.post(url,json={'title': 'a' * 200,'description': 'a' * 200, 'category_doc_id': 200})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'title': assert x['msg'] == 'ensure this value has at most 100 characters'

        # check all field type data
        response = client.post(url,json={'title': 123, 'description': 123, 'category_doc_id': 'asd'})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'title': assert x['msg'] == 'str type expected'
            if x['loc'][-1] == 'description': assert x['msg'] == 'str type expected'
            if x['loc'][-1] == 'category_doc_id': assert x['msg'] == 'value is not a valid integer'

    @pytest.mark.asyncio
    async def test_create_documentation(self,async_client):
        response = await async_client.post('/users/login',json={
            'email': self.account_2['email'],
            'password': self.account_2['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = self.prefix + '/create'
        category_doc_id = await self.get_category_doc_id(self.name)

        # check user is admin
        response = await async_client.post(url,headers={'X-CSRF-TOKEN': csrf_access_token},json={
            'title': self.name,
            'description': 'a' * 20,
            'category_doc_id': category_doc_id
        })
        assert response.status_code == 401
        assert response.json() == {"detail": "Only users with admin privileges can do this action."}

        # user admin login
        response = await async_client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': self.account_1['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        # category-doc not found
        response = await async_client.post(url,headers={'X-CSRF-TOKEN': csrf_access_token},json={
            'title': self.name,
            'description': 'a' * 20,
            'category_doc_id': 99999999
        })
        assert response.status_code == 404
        assert response.json() == {"detail": "Category-doc not found!"}

        response = await async_client.post(url,headers={'X-CSRF-TOKEN': csrf_access_token},json={
            'title': self.name,
            'description': 'a' * 20,
            'category_doc_id': category_doc_id
        })

        assert response.status_code == 201
        assert response.json() == {"detail": "Successfully add a new documentation."}

    @pytest.mark.asyncio
    async def test_title_duplicate_create_documentation(self,async_client):
        response = await async_client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': self.account_1['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = self.prefix + '/create'
        category_doc_id = await self.get_category_doc_id(self.name)

        response = await async_client.post(url,headers={'X-CSRF-TOKEN': csrf_access_token},json={
            'title': self.name,
            'description': 'a' * 20,
            'category_doc_id': category_doc_id
        })
        assert response.status_code == 400
        assert response.json() == {"detail": "The name has already been taken."}

    def test_get_all_documentations(self,client):
        url = self.prefix + '/all-documentations'

        # all field blank
        response = client.get(url + '?q=')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'q': assert x['msg'] == 'ensure this value has at least 1 characters'

        response = client.get(url + '?q=' + self.name)
        assert response.status_code == 200
        assert "documentations_description" in response.json()[0]

        # check data exists and type data
        assert type(response.json()[0]['documentations_id']) == int
        assert type(response.json()[0]['documentations_title']) == str
        assert type(response.json()[0]['documentations_slug']) == str
        assert type(response.json()[0]['documentations_description']) == str
        assert type(response.json()[0]['category_docs_id']) == int
        assert type(response.json()[0]['category_docs_name']) == str

    def test_validation_search_documentations_by_name(self,client):
        url = self.prefix + '/search-by-name'

        # field required
        response = client.get(url)
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'q': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'limit': assert x['msg'] == 'field required'

        # all field blank
        response = client.get(url + '?q=&limit=0')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'q': assert x['msg'] == 'ensure this value has at least 1 characters'
            if x['loc'][-1] == 'limit': assert x['msg'] == 'ensure this value is greater than 0'

        # check all field type data
        response = client.get(url + '?q=123&limit=asd')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'limit': assert x['msg'] == 'value is not a valid integer'

    def test_search_documentations_by_name(self,client):
        url = self.prefix + '/search-by-name'

        response = client.get(url + '?q=' + self.name + '&limit=1')
        assert response.status_code == 200
        assert "documentations_description" not in response.json()[0]

        # check data exists and type data
        assert type(response.json()[0]['documentations_id']) == int
        assert type(response.json()[0]['documentations_title']) == str
        assert type(response.json()[0]['documentations_slug']) == str
        assert type(response.json()[0]['category_docs_id']) == int
        assert type(response.json()[0]['category_docs_name']) == str

    def test_get_documentation_by_slug(self,client):
        url = self.prefix + '/'

        # documentation not found
        response = client.get(url + '0')
        assert response.status_code == 404
        assert response.json() == {"detail": "Documentation not found!"}

        response = client.get(url + self.name)
        assert response.status_code == 200
        assert "documentations_id" in response.json()
        assert "documentations_title" in response.json()
        assert "documentations_slug" in response.json()
        assert "documentations_description" in response.json()
        assert "category_docs_id" in response.json()
        assert "category_docs_name" in response.json()

    def test_validation_update_documentation(self,client):
        url = self.prefix + '/update/'

        # field required
        response = client.put(url + '0',json={})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'title': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'description': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'category_doc_id': assert x['msg'] == 'field required'

        # all field blank
        response = client.put(url + '0',json={'title': ' ','description': ' ','category_doc_id': 0})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'documentation_id': assert x['msg'] == 'ensure this value is greater than 0'
            if x['loc'][-1] == 'title': assert x['msg'] == 'ensure this value has at least 3 characters'
            if x['loc'][-1] == 'description': assert x['msg'] == 'ensure this value has at least 20 characters'
            if x['loc'][-1] == 'category_doc_id': assert x['msg'] == 'ensure this value is greater than 0'

        # test limit value
        response = client.put(url + '1',json={'title': 'a' * 200,'description': 'a' * 200, 'category_doc_id': 200})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'title': assert x['msg'] == 'ensure this value has at most 100 characters'

        # check all field type data
        response = client.put(url + 'a',json={'title': 123, 'description': 123, 'category_doc_id': 'asd'})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'documentation_id': assert x['msg'] == 'value is not a valid integer'
            if x['loc'][-1] == 'title': assert x['msg'] == 'str type expected'
            if x['loc'][-1] == 'description': assert x['msg'] == 'str type expected'
            if x['loc'][-1] == 'category_doc_id': assert x['msg'] == 'value is not a valid integer'

    @pytest.mark.asyncio
    async def test_update_documentation(self,async_client):
        response = await async_client.post('/users/login',json={
            'email': self.account_2['email'],
            'password': self.account_2['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = self.prefix + '/update/'
        category_doc_id = await self.get_category_doc_id(self.name)
        documentation_id = await self.get_documentation_id(self.name)

        # check user is admin
        response = await async_client.put(url + str(documentation_id),json={
            'title': self.name,
            'description': 'a' * 20,
            'category_doc_id': category_doc_id
        },headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 401
        assert response.json() == {"detail": "Only users with admin privileges can do this action."}

        # user admin login
        response = await async_client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': self.account_1['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        # documentation not found
        response = await async_client.put(url + '9' * 8,json={
            'title': self.name,
            'description': 'a' * 20,
            'category_doc_id': category_doc_id
        },headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 404
        assert response.json() == {"detail": "Documentation not found!"}

        # category doc not found
        response = await async_client.put(url + str(documentation_id),json={
            'title': self.name,
            'description': 'a' * 20,
            'category_doc_id': 99999999
        },headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 404
        assert response.json() == {"detail": "Category-doc not found!"}

        response = await async_client.put(url + str(documentation_id),json={
            'title': self.name,
            'description': 'a' * 20,
            'category_doc_id': category_doc_id
        },headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 200
        assert response.json() == {"detail": "Successfully update the documentation."}

    @pytest.mark.asyncio
    async def test_title_duplicate_update_documentation(self,async_client):
        # user admin login
        response = await async_client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': self.account_1['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        category_doc_id = await self.get_category_doc_id(self.name)
        documentation_id = await self.get_documentation_id(self.name)

        url = self.prefix + '/create'

        # create another documentation
        response = await async_client.post(url,headers={'X-CSRF-TOKEN': csrf_access_token},json={
            'title': self.name2,
            'description': 'a' * 20,
            'category_doc_id': category_doc_id
        })
        assert response.status_code == 201
        assert response.json() == {"detail": "Successfully add a new documentation."}

        url = self.prefix + '/update/'

        # name already taken
        response = await async_client.put(url + str(documentation_id),headers={'X-CSRF-TOKEN': csrf_access_token},json={
            'title': self.name2,
            'description': 'a' * 20,
            'category_doc_id': category_doc_id
        })
        assert response.status_code == 400
        assert response.json() == {"detail": "The name has already been taken."}

    def test_validation_delete_documentation(self,client):
        url = self.prefix + '/delete/'
        # all field blank
        response = client.delete(url + '0')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'documentation_id': assert x['msg'] == 'ensure this value is greater than 0'
        # check all field type data
        response = client.delete(url + 'a')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'documentation_id': assert x['msg'] == 'value is not a valid integer'

    @pytest.mark.asyncio
    async def test_delete_documentation(self,async_client):
        response = await async_client.post('/users/login',json={
            'email': self.account_2['email'],
            'password': self.account_2['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = self.prefix + '/delete/'

        documentation_id = await self.get_documentation_id(self.name)

        # check user is admin
        response = await async_client.delete(url + str(documentation_id),headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 401
        assert response.json() == {"detail": "Only users with admin privileges can do this action."}

        # user admin login
        response = await async_client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': self.account_1['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        # documentation not found
        response = await async_client.delete(url + '9' * 8,headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 404
        assert response.json() == {"detail": "Documentation not found!"}

        # delete documentation one
        response = await async_client.delete(url + str(documentation_id),headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 200
        assert response.json() == {"detail": "Successfully delete the documentation."}

        documentation_id = await self.get_documentation_id(self.name2)

        response = await async_client.delete(url + str(documentation_id),headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 200
        assert response.json() == {"detail": "Successfully delete the documentation."}

    @pytest.mark.asyncio
    async def test_delete_category_doc(self,async_client):
        response = await async_client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': self.account_1['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = '/category-docs/delete/'
        category_doc_id = await self.get_category_doc_id(self.name)

        response = await async_client.delete(url + str(category_doc_id),headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 200
        assert response.json() == {"detail": "Successfully delete the category-doc."}

        # user admin login
        response = await async_client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': self.account_1['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

    @pytest.mark.asyncio
    async def test_delete_user_from_db(self,async_client):
        await self.delete_user_from_db()
