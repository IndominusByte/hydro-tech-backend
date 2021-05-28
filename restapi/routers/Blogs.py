from fastapi import APIRouter, Path, Depends, HTTPException
from fastapi_jwt_auth import AuthJWT
from controllers.BlogController import BlogFetch, BlogCrud
from controllers.UserController import UserFetch
from dependencies.BlogDependant import create_form_blog, get_all_query_blog, update_form_blog
from schemas.blogs.BlogSchema import BlogPaginate, BlogData
from models.BlogModel import blog as blog_model
from libs.MagicImage import MagicImage
from libs.Visitor import Visitor
from slugify import slugify

router = APIRouter()

@router.post('/create',status_code=201,
    responses={
        201: {
            "description": "Successful Response",
            "content": {"application/json":{"example": {"detail": "Successfully add a new blog."}}}
        },
        400: {
            "description": "Name already taken",
            "content": {"application/json":{"example": {"detail": "The name has already been taken."}}}
        },
        401: {
            "description": "User without role admin",
            "content": {"application/json": {"example": {"detail": "Only users with admin privileges can do this action."}}}
        },
        413: {
            "description": "Request Entity Too Large",
            "content": {"application/json": {"example": {"detail": "An image cannot greater than {max_file_size} Mb."}}}
        }
    }
)
async def create_blog(form_data: create_form_blog = Depends(), authorize: AuthJWT = Depends()):
    authorize.jwt_required()

    user_id = int(authorize.get_jwt_subject())
    await UserFetch.user_is_admin(user_id)

    form_data['slug'] = slugify(form_data['title'])

    if await BlogFetch.filter_by_slug(form_data['slug']):
        raise HTTPException(status_code=400,detail="The name has already been taken.")

    magic_image = MagicImage(file=form_data['image'].file,width=600,height=400,path_upload='blogs/')
    magic_image.save_image()
    form_data['image'] = magic_image.file_name

    await BlogCrud.create_blog(**form_data)

    return {"detail": "Successfully add a new blog."}

@router.get('/all-blogs',response_model=BlogPaginate)
async def get_all_blogs(query_string: get_all_query_blog = Depends()):
    return await BlogFetch.get_all_blog_paginate(**query_string)

@router.get('/{slug}',response_model=BlogData,
    responses={
        404: {
            "description": "Blog not found",
            "content": {"application/json": {"example": {"detail": "Blog not found!"}}}
        }
    }
)
async def get_blog_by_slug(slug: str = Path(...,min_length=1), visitor: Visitor = Depends()):
    if blog := await BlogFetch.filter_by_slug(slug):
        await visitor.increment_visitor(table=blog_model,id_=blog['id'])  # set visitor
        return {f"blogs_{index}":value for index,value in blog.items()}
    raise HTTPException(status_code=404,detail="Blog not found!")

@router.put('/update/{blog_id}',
    responses={
        200: {
            "description": "Successful Response",
            "content": {"application/json":{"example": {"detail": "Successfully update the blog."}}}
        },
        400: {
            "description": "Name already taken",
            "content": {"application/json":{"example": {"detail": "The name has already been taken."}}}
        },
        401: {
            "description": "User without role admin",
            "content": {"application/json": {"example": {"detail": "Only users with admin privileges can do this action."}}}
        },
        404: {
            "description": "Blog not found",
            "content": {"application/json": {"example": {"detail": "Blog not found!"}}}
        },
        413: {
            "description": "Request Entity Too Large",
            "content": {"application/json": {"example": {"detail": "An image cannot greater than {max_file_size} Mb."}}}
        }
    }
)
async def update_blog(
    blog_id: int = Path(...,gt=0),
    form_data: update_form_blog = Depends(),
    authorize: AuthJWT = Depends()
):
    authorize.jwt_required()

    user_id = int(authorize.get_jwt_subject())
    await UserFetch.user_is_admin(user_id)

    if blog := await BlogFetch.filter_by_id(blog_id):
        form_data['slug'] = slugify(form_data['title'])

        if blog['slug'] != form_data['slug'] and await BlogFetch.filter_by_slug(form_data['slug']):
            raise HTTPException(status_code=400,detail="The name has already been taken.")

        # delete the image from db if file exists
        if image := form_data['image']:
            MagicImage.delete_image(file=blog['image'],path_delete='blogs/')
            magic_image = MagicImage(file=image.file,width=600,height=400,path_upload='blogs/')
            magic_image.save_image()
            form_data['image'] = magic_image.file_name
        else: form_data.pop('image')

        await BlogCrud.update_blog(blog['id'],**form_data)
        return {"detail": "Successfully update the blog."}
    raise HTTPException(status_code=404,detail="Blog not found!")

@router.delete('/delete/{blog_id}',
    responses={
        200: {
            "description": "Successful Response",
            "content": {"application/json":{"example": {"detail": "Successfully delete the blog."}}}
        },
        401: {
            "description": "User without role admin",
            "content": {"application/json": {"example": {"detail": "Only users with admin privileges can do this action."}}}
        },
        404: {
            "description": "Blog not found",
            "content": {"application/json": {"example": {"detail": "Blog not found!"}}}
        },
    }
)
async def delete_blog(blog_id: int = Path(...,gt=0), authorize: AuthJWT = Depends()):
    authorize.jwt_required()

    user_id = int(authorize.get_jwt_subject())
    await UserFetch.user_is_admin(user_id)

    if blog := await BlogFetch.filter_by_id(blog_id):
        MagicImage.delete_image(file=blog['image'],path_delete='blogs/')
        await BlogCrud.delete_blog(blog['id'])
        return {"detail": "Successfully delete the blog."}
    raise HTTPException(status_code=404,detail="Blog not found!")
