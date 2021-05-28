from fastapi import APIRouter, Query, Path, Depends, HTTPException
from fastapi_jwt_auth import AuthJWT
from controllers.CategoryDocController import CategoryDocFetch, CategoryDocCrud
from controllers.UserController import UserFetch
from schemas.category_docs.CategoryDocSchema import CategoryDocCreateUpdate, CategoryDocData
from typing import List

router = APIRouter()

@router.post('/create',status_code=201,
    responses={
        201: {
            "description": "Successful Response",
            "content": {"application/json":{"example": {"detail": "Successfully add a new category-doc."}}}
        },
        400: {
            "description": "Name already taken",
            "content": {"application/json":{"example": {"detail": "The name has already been taken."}}}
        },
        401: {
            "description": "User without role admin",
            "content": {"application/json": {"example": {"detail": "Only users with admin privileges can do this action."}}}
        },
    }
)
async def create_category_doc(category_doc: CategoryDocCreateUpdate, authorize: AuthJWT = Depends()):
    authorize.jwt_required()

    user_id = int(authorize.get_jwt_subject())
    await UserFetch.user_is_admin(user_id)

    if await CategoryDocFetch.filter_by_name(category_doc.name):
        raise HTTPException(status_code=400,detail="The name has already been taken.")

    await CategoryDocCrud.create_category_doc(category_doc.name)
    return {"detail": "Successfully add a new category-doc."}

@router.get('/all-category-docs',response_model=List[CategoryDocData])
async def get_all_category_docs(q: str = Query(None,min_length=1)):
    return await CategoryDocFetch.get_all_category_docs(q)

@router.get('/get-category-doc/{category_doc_id}',response_model=CategoryDocData,
    responses={
        404: {
            "description": "Category-doc not found",
            "content": {"application/json": {"example": {"detail": "Category-doc not found!"}}}
        }
    }
)
async def get_category_doc_by_id(category_doc_id: int = Path(...,gt=0)):
    if category_doc := await CategoryDocFetch.filter_by_id(category_doc_id):
        return {f"category_docs_{index}":value for index,value in category_doc.items()}
    raise HTTPException(status_code=404,detail="Category-doc not found!")

@router.put('/update/{category_doc_id}',
    responses={
        200: {
            "description": "Successful Response",
            "content": {"application/json":{"example": {"detail": "Successfully update the category-doc."}}}
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
async def update_category_doc(
    category_doc_data: CategoryDocCreateUpdate,
    category_doc_id: int = Path(...,gt=0),
    authorize: AuthJWT = Depends()
):
    authorize.jwt_required()

    user_id = int(authorize.get_jwt_subject())
    await UserFetch.user_is_admin(user_id)

    if category_doc := await CategoryDocFetch.filter_by_id(category_doc_id):
        if category_doc['name'] != category_doc_data.name and await CategoryDocFetch.filter_by_name(category_doc_data.name):
            raise HTTPException(status_code=400,detail="The name has already been taken.")

        await CategoryDocCrud.update_category_doc(category_doc['id'],name=category_doc_data.name)
        return {"detail": "Successfully update the category-doc."}
    raise HTTPException(status_code=404,detail="Category-doc not found!")

@router.delete('/delete/{category_doc_id}',
    responses={
        200: {
            "description": "Successful Response",
            "content": {"application/json":{"example": {"detail": "Successfully delete the category-doc."}}}
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
async def delete_category_doc(category_doc_id: int = Path(...,gt=0), authorize: AuthJWT = Depends()):
    authorize.jwt_required()

    user_id = int(authorize.get_jwt_subject())
    await UserFetch.user_is_admin(user_id)

    if category_doc := await CategoryDocFetch.filter_by_id(category_doc_id):
        await CategoryDocCrud.delete_category_doc(category_doc['id'])
        return {"detail": "Successfully delete the category-doc."}
    raise HTTPException(status_code=404,detail="Category-doc not found!")
