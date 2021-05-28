from fastapi import APIRouter, Path, Depends, HTTPException
from fastapi_jwt_auth import AuthJWT
from controllers.PlantController import PlantFetch, PlantCrud
from controllers.UserController import UserFetch
from dependencies.PlantDependant import create_form_plant, update_form_plant, get_all_query_plant
from schemas.plants.PlantSchema import PlantPaginate, PlantData
from libs.MagicImage import MagicImage

router = APIRouter()

@router.post('/create',status_code=201,
    responses={
        201: {
            "description": "Successful Response",
            "content": {"application/json":{"example": {"detail": "Successfully add a new plant."}}}
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
async def create_plant(form_data: create_form_plant = Depends(), authorize: AuthJWT = Depends()):
    authorize.jwt_required()

    user_id = int(authorize.get_jwt_subject())
    await UserFetch.user_is_admin(user_id)

    if await PlantFetch.filter_by_name(form_data['name']):
        raise HTTPException(status_code=400,detail="The name has already been taken.")

    magic_image = MagicImage(file=form_data['image'].file,width=500,height=500,path_upload='plants/',square=True)
    magic_image.save_image()
    form_data['image'] = magic_image.file_name

    await PlantCrud.create_plant(**form_data)

    return {"detail": "Successfully add a new plant."}

@router.get('/all-plants',response_model=PlantPaginate)
async def get_all_plants(query_string: get_all_query_plant = Depends()):
    return await PlantFetch.get_all_plants_paginate(**query_string)

@router.get('/get-plant/{plant_id}',response_model=PlantData,
    responses={
        404: {
            "description": "Plants not found",
            "content": {"application/json": {"example": {"detail": "Plants not found!"}}}
        }
    }
)
async def get_plant_by_id(plant_id: int = Path(...,gt=0)):
    if plant := await PlantFetch.filter_by_id(plant_id):
        return {f"plants_{index}":value for index,value in plant.items()}
    raise HTTPException(status_code=404,detail="Plants not found!")

@router.put('/update/{plant_id}',
    responses={
        200: {
            "description": "Successful Response",
            "content": {"application/json":{"example": {"detail": "Successfully update the plant."}}}
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
            "description": "Plants not found",
            "content": {"application/json": {"example": {"detail": "Plants not found!"}}}
        },
        413: {
            "description": "Request Entity Too Large",
            "content": {"application/json": {"example": {"detail": "An image cannot greater than {max_file_size} Mb."}}}
        }
    }
)
async def update_plant(
    plant_id: int = Path(...,gt=0),
    form_data: update_form_plant = Depends(),
    authorize: AuthJWT = Depends()
):
    authorize.jwt_required()

    user_id = int(authorize.get_jwt_subject())
    await UserFetch.user_is_admin(user_id)

    if plant := await PlantFetch.filter_by_id(plant_id):
        if plant['name'] != form_data['name'] and await PlantFetch.filter_by_name(form_data['name']):
            raise HTTPException(status_code=400,detail="The name has already been taken.")

        # delete the image from db if file exists
        if image := form_data['image']:
            MagicImage.delete_image(file=plant['image'],path_delete='plants/')
            magic_image = MagicImage(file=image.file,width=500,height=500,path_upload='plants/',square=True)
            magic_image.save_image()
            form_data['image'] = magic_image.file_name
        else: form_data.pop('image')

        await PlantCrud.update_plant(plant['id'],**form_data)
        return {"detail": "Successfully update the plant."}
    raise HTTPException(status_code=404,detail="Plants not found!")

@router.delete('/delete/{plant_id}',
    responses={
        200: {
            "description": "Successful Response",
            "content": {"application/json":{"example": {"detail": "Successfully delete the plant."}}}
        },
        401: {
            "description": "User without role admin",
            "content": {"application/json": {"example": {"detail": "Only users with admin privileges can do this action."}}}
        },
        404: {
            "description": "Plants not found",
            "content": {"application/json": {"example": {"detail": "Plants not found!"}}}
        },
    }
)
async def delete_plant(plant_id: int = Path(...,gt=0), authorize: AuthJWT = Depends()):
    authorize.jwt_required()

    user_id = int(authorize.get_jwt_subject())
    await UserFetch.user_is_admin(user_id)

    if plant := await PlantFetch.filter_by_id(plant_id):
        MagicImage.delete_image(file=plant['image'],path_delete='plants/')
        await PlantCrud.delete_plant(plant['id'])
        return {"detail": "Successfully delete the plant."}
    raise HTTPException(status_code=404,detail="Plants not found!")
