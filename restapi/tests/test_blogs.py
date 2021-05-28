import pytest
from pathlib import Path
from .operationtest import OperationTest

class TestBlog(OperationTest):
    prefix = "/blogs"

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

    def test_validation_create_blog(self,client):
        url = self.prefix + '/create'

        # field required
        response = client.post(url,data={})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'image': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'title': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'description': assert x['msg'] == 'field required'

        # all field blank
        response = client.post(url,data={
            'title': ' ',
            'description': ' '
        })
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'title': assert x['msg'] == 'ensure this value has at least 3 characters'
            if x['loc'][-1] == 'description': assert x['msg'] == 'ensure this value has at least 20 characters'

        # test limit value
        response = client.post(url,data={
            'title': 'a' * 200,
            'description': 'a' * 200
        })
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'title': assert x['msg'] == 'ensure this value has at most 100 characters'

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
    async def test_create_blog(self,async_client):
        response = await async_client.post('/users/login',json={
            'email': self.account_2['email'],
            'password': self.account_2['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = self.prefix + '/create'

        # check user is admin
        with open(self.test_image_dir + 'image.jpeg','rb') as tmp:
            response = await async_client.post(
                url,
                data={'title': self.name,'description': 'a' * 20},
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
            response = await async_client.post(
                url,
                data={'title': self.name,'description': 'a' * 20},
                files={'image': tmp},
                headers={'X-CSRF-TOKEN': csrf_access_token}
            )
            assert response.status_code == 201
            assert response.json() == {"detail": "Successfully add a new blog."}

        # check image exists in directory
        image = await self.get_blog_image(self.name)
        assert Path(self.blog_dir + image).is_file() is True

    def test_title_duplicate_create_blog(self,client):
        response = client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': self.account_1['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = self.prefix + '/create'

        with open(self.test_image_dir + 'image.jpeg','rb') as tmp:
            response = client.post(
                url,
                data={'title': self.name,'description': 'a' * 20},
                files={'image': tmp},
                headers={'X-CSRF-TOKEN': csrf_access_token}
            )
            assert response.status_code == 400
            assert response.json() == {"detail": "The name has already been taken."}

    def test_validation_get_all_blogs(self,client):
        url = self.prefix + '/all-blogs'
        # field required
        response = client.get(url)
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'page': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'per_page': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'order_by': assert x['msg'] == 'field required'

        # all field blank
        response = client.get(url + '?page=0&per_page=0&q=&order_by=')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'page': assert x['msg'] == 'ensure this value is greater than 0'
            if x['loc'][-1] == 'per_page': assert x['msg'] == 'ensure this value is greater than 0'
            if x['loc'][-1] == 'q': assert x['msg'] == 'ensure this value has at least 1 characters'

        # check all field type data
        response = client.get(url + '?page=a&per_page=a&q=123&order_by=123')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'page': assert x['msg'] == 'value is not a valid integer'
            if x['loc'][-1] == 'per_page': assert x['msg'] == 'value is not a valid integer'
            if x['loc'][-1] == 'order_by': assert x['msg'] == "unexpected value; permitted: 'newest', 'oldest', 'visitor'"

    def test_get_all_blogs(self,client):
        url = self.prefix + '/all-blogs'

        response = client.get(url + '?page=1&per_page=1&order_by=newest')
        assert response.status_code == 200
        assert 'data' in response.json()
        assert 'total' in response.json()
        assert 'next_num' in response.json()
        assert 'prev_num' in response.json()
        assert 'page' in response.json()
        assert 'iter_pages' in response.json()

        # check data exists and type data
        assert type(response.json()['data'][0]['blogs_id']) == int
        assert type(response.json()['data'][0]['blogs_title']) == str
        assert type(response.json()['data'][0]['blogs_slug']) == str
        assert type(response.json()['data'][0]['blogs_image']) == str
        assert type(response.json()['data'][0]['blogs_description']) == str
        assert type(response.json()['data'][0]['blogs_visitor']) == str
        assert type(response.json()['data'][0]['blogs_created_at']) == str
        assert type(response.json()['data'][0]['blogs_updated_at']) == str

    def test_get_blog_by_slug(self,client):
        url = self.prefix + '/'

        # blog not found
        response = client.get(url + '0')
        assert response.status_code == 404
        assert response.json() == {"detail": "Blog not found!"}

        response = client.get(url + self.name)
        assert response.status_code == 200
        assert "blogs_id" in response.json()
        assert "blogs_title" in response.json()
        assert "blogs_slug" in response.json()
        assert "blogs_image" in response.json()
        assert "blogs_description" in response.json()
        assert "blogs_visitor" in response.json()
        assert "blogs_created_at" in response.json()
        assert "blogs_updated_at" in response.json()

    def test_validation_update_blog(self,client):
        url = self.prefix + '/update/'

        # field required
        response = client.put(url + '0',data={})
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'image': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'title': assert x['msg'] == 'field required'
            if x['loc'][-1] == 'description': assert x['msg'] == 'field required'

        # all field blank
        response = client.put(url + '0',data={
            'title': ' ',
            'description': ' '
        })
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'blog_id': assert x['msg'] == 'ensure this value is greater than 0'
            if x['loc'][-1] == 'title': assert x['msg'] == 'ensure this value has at least 3 characters'
            if x['loc'][-1] == 'description': assert x['msg'] == 'ensure this value has at least 20 characters'

        # test limit value
        response = client.put(url + '1',data={
            'title': 'a' * 200,
            'description': 'a' * 200
        })
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'title': assert x['msg'] == 'ensure this value has at most 100 characters'

        # check all field type data
        response = client.put(url + 'a',data={
            'title': 123,
            'description': 123
        })
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'blog_id': assert x['msg'] == 'value is not a valid integer'

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
    async def test_update_blog(self,async_client):
        response = await async_client.post('/users/login',json={
            'email': self.account_2['email'],
            'password': self.account_2['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = self.prefix + '/update/'
        blog_id = await self.get_blog_id(self.name)

        # check user is admin
        response = await async_client.put(url + str(blog_id),
            data={'title': self.name, 'description': 'a' * 20},
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

        # blog not found
        response = await async_client.put(url + '9' * 8,
            data={'title': self.name, 'description': 'a' * 20},
            headers={'X-CSRF-TOKEN': csrf_access_token}
        )
        assert response.status_code == 404
        assert response.json() == {"detail": "Blog not found!"}

        image = await self.get_blog_image(self.name)

        with open(self.test_image_dir + 'image.jpeg','rb') as tmp:
            response = await async_client.put(url + str(blog_id),
                data={'title': self.name, 'description': 'a' * 20},
                headers={'X-CSRF-TOKEN': csrf_access_token},
                files={'image': tmp}
            )
            assert response.status_code == 200
            assert response.json() == {"detail": "Successfully update the blog."}

        # check the previous image doesn't exists in directory
        assert Path(self.blog_dir + image).is_file() is False

    @pytest.mark.asyncio
    async def test_name_duplicate_update_blog(self,async_client):
        # user admin login
        response = await async_client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': self.account_1['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = self.prefix + '/create'

        with open(self.test_image_dir + 'image.jpeg','rb') as tmp:
            response = await async_client.post(
                url,
                data={'title': self.name2,'description': 'a' * 20},
                files={'image': tmp},
                headers={'X-CSRF-TOKEN': csrf_access_token}
            )
            assert response.status_code == 201
            assert response.json() == {"detail": "Successfully add a new blog."}

        url = self.prefix + '/update/'
        blog_id = await self.get_blog_id(self.name2)

        # name already taken
        with open(self.test_image_dir + 'image.jpeg','rb') as tmp:
            response = await async_client.put(url + str(blog_id),
                data={'title': self.name, 'description': 'a' * 20},
                headers={'X-CSRF-TOKEN': csrf_access_token},
                files={'image': tmp}
            )
            assert response.status_code == 400
            assert response.json() == {"detail": "The name has already been taken."}

    def test_validation_delete_blog(self,client):
        url = self.prefix + '/delete/'
        # all field blank
        response = client.delete(url + '0')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'blog_id': assert x['msg'] == 'ensure this value is greater than 0'
        # check all field type data
        response = client.delete(url + 'a')
        assert response.status_code == 422
        for x in response.json()['detail']:
            if x['loc'][-1] == 'blog_id': assert x['msg'] == 'value is not a valid integer'

    @pytest.mark.asyncio
    async def test_delete_blog(self,async_client):
        response = await async_client.post('/users/login',json={
            'email': self.account_2['email'],
            'password': self.account_2['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        url = self.prefix + '/delete/'

        blog_id = await self.get_blog_id(self.name)
        image = await self.get_blog_image(self.name)

        # check user is admin
        response = await async_client.delete(url + str(blog_id),headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 401
        assert response.json() == {"detail": "Only users with admin privileges can do this action."}

        # user admin login
        response = await async_client.post('/users/login',json={
            'email': self.account_1['email'],
            'password': self.account_1['password']
        })
        csrf_access_token = response.cookies.get('csrf_access_token')

        # blog not found
        response = await async_client.delete(url + '9' * 8,headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 404
        assert response.json() == {"detail": "Blog not found!"}

        # delete blog one
        response = await async_client.delete(url + str(blog_id),headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 200
        assert response.json() == {"detail": "Successfully delete the blog."}
        # check image has been delete in directory
        assert Path(self.blog_dir + image).is_file() is False

        # delete blog two
        blog_id = await self.get_blog_id(self.name2)
        image = await self.get_blog_image(self.name2)

        response = await async_client.delete(url + str(blog_id),headers={'X-CSRF-TOKEN': csrf_access_token})
        assert response.status_code == 200
        assert response.json() == {"detail": "Successfully delete the blog."}
        # check image has been delete in directory
        assert Path(self.blog_dir + image).is_file() is False

    @pytest.mark.asyncio
    async def test_delete_user_from_db(self,async_client):
        await self.delete_user_from_db()
