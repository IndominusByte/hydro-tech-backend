from fastapi import APIRouter, Query, Path, Depends, HTTPException
from fastapi_jwt_auth import AuthJWT
from controllers.UserController import UserFetch
from controllers.DocumentationController import DocumentationFetch, DocumentationCrud
from controllers.CategoryDocController import CategoryDocFetch
from schemas.documentations.DocumentationSchema import (
    DocumentationCreateUpdate,
    DocumentationData,
    DocumentationSearchByName
)
from slugify import slugify
from typing import List

router = APIRouter()

@router.post('/create',status_code=201,
    responses={
        201: {
            "description": "Successful Response",
            "content": {"application/json":{"example": {"detail": "Successfully add a new documentation."}}}
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
            "description": "Category-doc not found",
            "content": {"application/json": {"example": {"detail": "Category-doc not found!"}}}
        },
    }
)
async def create_documentation(documentation: DocumentationCreateUpdate, authorize: AuthJWT = Depends()):
    authorize.jwt_required()

    user_id = int(authorize.get_jwt_subject())
    await UserFetch.user_is_admin(user_id)

    slug = slugify(documentation.title)

    if await DocumentationFetch.filter_by_slug(slug):
        raise HTTPException(status_code=400,detail="The name has already been taken.")

    if not await CategoryDocFetch.filter_by_id(documentation.category_doc_id):
        raise HTTPException(status_code=404,detail="Category-doc not found!")

    await DocumentationCrud.create_documentation(**documentation.dict(),slug=slug)
    return {"detail": "Successfully add a new documentation."}

@router.get('/all-documentations',response_model=List[DocumentationData])
async def get_all_documentations(q: str = Query(None,min_length=1)):
    return await DocumentationFetch.get_all_documentations(q)

@router.get('/search-by-name',response_model=List[DocumentationSearchByName])
async def search_documentations_by_name(q: str = Query(...,min_length=1), limit: int = Query(...,gt=0)):
    return await DocumentationFetch.search_documentations_by_name(q=q,limit=limit)

@router.get('/{slug}',response_model=DocumentationData,
    responses={
        404: {
            "description": "Documentation not found",
            "content": {"application/json": {"example": {"detail": "Documentation not found!"}}}
        }
    }
)
async def get_documentation_by_slug(slug: str = Path(...,min_length=1)):
    if documentation := await DocumentationFetch.filter_by_slug(slug):
        return {index:value for index,value in documentation.items()}
    raise HTTPException(status_code=404,detail="Documentation not found!")

@router.put('/update/{documentation_id}',
    responses={
        200: {
            "description": "Successful Response",
            "content": {"application/json":{"example": {"detail": "Successfully update the documentation."}}}
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
            "description": "Category-doc & Documentation not found",
            "content": {"application/json": {"example": {"detail": "string"}}}
        },
    }
)
async def update_documentation(
    documentation_data: DocumentationCreateUpdate,
    documentation_id: int = Path(...,gt=0),
    authorize: AuthJWT = Depends()
):
    authorize.jwt_required()

    user_id = int(authorize.get_jwt_subject())
    await UserFetch.user_is_admin(user_id)

    if documentation := await DocumentationFetch.filter_by_id(documentation_id):
        slug = slugify(documentation_data.title)

        if documentation['slug'] != slug and await DocumentationFetch.filter_by_slug(slug):
            raise HTTPException(status_code=400,detail="The name has already been taken.")

        if not await CategoryDocFetch.filter_by_id(documentation_data.category_doc_id):
            raise HTTPException(status_code=404,detail="Category-doc not found!")

        await DocumentationCrud.update_documentation(documentation['id'],**documentation_data.dict(),slug=slug)
        return {"detail": "Successfully update the documentation."}
    raise HTTPException(status_code=404,detail="Documentation not found!")

@router.delete('/delete/{documentation_id}',
    responses={
        200: {
            "description": "Successful Response",
            "content": {"application/json":{"example": {"detail": "Successfully delete the documentation."}}}
        },
        401: {
            "description": "User without role admin",
            "content": {"application/json": {"example": {"detail": "Only users with admin privileges can do this action."}}}
        },
        404: {
            "description": "Documentation not found",
            "content": {"application/json": {"example": {"detail": "Documentation not found!"}}}
        },
    }
)
async def delete_documentation(documentation_id: int = Path(...,gt=0), authorize: AuthJWT = Depends()):
    authorize.jwt_required()

    user_id = int(authorize.get_jwt_subject())
    await UserFetch.user_is_admin(user_id)

    if documentation := await DocumentationFetch.filter_by_id(documentation_id):
        await DocumentationCrud.delete_documentation(documentation['id'])
        return {"detail": "Successfully delete the documentation."}
    raise HTTPException(status_code=404,detail="Documentation not found!")
