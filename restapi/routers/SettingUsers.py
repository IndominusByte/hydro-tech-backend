from fastapi import APIRouter, Path, Request, Depends, HTTPException
from fastapi_jwt_auth import AuthJWT
from controllers.SettingUserController import SettingUserCrud, SettingUserFetch
from controllers.UserController import UserFetch
from controllers.PlantController import PlantFetch
from controllers.ReportController import ReportCrud
from controllers.GrowthPlantController import GrowthPlantCrud
from controllers.AlertController import AlertCrud, AlertLogic
from schemas.setting_users.SettingUserSchema import (
    SettingUserCreate,
    SettingUserChangeToken,
    SettingUserUpdate,
    SettingUserUpdateServo,
    SettingUserData,
    SettingUserPlantProgressData
)
from libs.MagicImage import MagicImage

router = APIRouter()

@router.post('/create',status_code=201,
    responses={
        201: {
            "description": "Successful Response",
            "content": {"application/json":{"example": {"detail": "Successfully create an setting."}}}
        },
        400: {
            "description": "Setting already exists",
            "content": {"application/json":{"example": {"detail": "User already had setting."}}}
        },
        404: {
            "description": "Plants not found",
            "content": {"application/json": {"example": {"detail": "Plants not found!"}}}
        },
    }
)
async def create_setting_user(setting_user: SettingUserCreate, authorize: AuthJWT = Depends()):
    authorize.jwt_required()

    user_id = int(authorize.get_jwt_subject())
    if user := await UserFetch.filter_by_id(user_id):
        if await SettingUserFetch.filter_by_user_id(user['id']):
            raise HTTPException(status_code=400,detail="User already had setting.")

        if not await PlantFetch.filter_by_id(setting_user.plant_id):
            raise HTTPException(status_code=404,detail="Plants not found!")

        authorize.get_raw_jwt(setting_user.token)

        await SettingUserCrud.create_setting_user(**setting_user.dict(),user_id=user['id'])
        return {"detail": "Successfully create an setting."}

@router.get('/progress-plant',response_model=SettingUserPlantProgressData)
async def progress_plant(authorize: AuthJWT = Depends()):
    authorize.jwt_required()

    user_id = int(authorize.get_jwt_subject())
    if user := await UserFetch.filter_by_id(user_id):
        results = await SettingUserFetch.get_progress_plant(user['id'])
        if results['percentage'] >= 90:
            if await AlertLogic.check_alert(user['id'],'ready_harvest') is False:
                await AlertCrud.create_alert(**{
                    'type': 'ready_harvest',
                    'message': 'Hey, it looks like your plants ready to harvest',
                    'user_id': user['id']
                })
        return results

@router.get('/my-setting',response_model=SettingUserData)
async def my_setting(authorize: AuthJWT = Depends()):
    authorize.jwt_required()

    user_id = int(authorize.get_jwt_subject())
    if user := await UserFetch.filter_by_id(user_id):
        return await SettingUserFetch.get_my_setting(user['id'])

@router.put('/change-camera',
    responses={
        200: {
            "description": "Successful Response",
            "content": {"application/json":{"example": {"detail": "Successfully change the camera to {camera}."}}}
        },
        404: {
            "description": "Setting not found",
            "content": {"application/json": {"example": {"detail": "Setting not found!"}}}
        },
    }
)
async def change_setting_camera(authorize: AuthJWT = Depends()):
    authorize.jwt_required()

    user_id = int(authorize.get_jwt_subject())
    if user := await UserFetch.filter_by_id(user_id):
        setting_user = await SettingUserFetch.filter_by_user_id(user['id'])

        if not setting_user:
            raise HTTPException(status_code=404,detail="Setting not found!")

        camera = not setting_user['camera']

        await SettingUserCrud.update_setting_user(user['id'],camera=camera)
        return {"detail": f"Successfully change the camera to {camera}."}

@router.put('/change-control-type',
    responses={
        200: {
            "description": "Successful Response",
            "content": {"application/json":{"example":{"detail": "Successfully change the control type to {control_type}."}}}
        },
        404: {
            "description": "Setting not found",
            "content": {"application/json": {"example": {"detail": "Setting not found!"}}}
        },
    }
)
async def change_setting_control_type(authorize: AuthJWT = Depends()):
    authorize.jwt_required()

    user_id = int(authorize.get_jwt_subject())
    if user := await UserFetch.filter_by_id(user_id):
        setting_user = await SettingUserFetch.filter_by_user_id(user['id'])

        if not setting_user:
            raise HTTPException(status_code=404,detail="Setting not found!")

        control_type = not setting_user['control_type']

        await SettingUserCrud.update_setting_user(user['id'],control_type=control_type)
        return {"detail": f"Successfully change the control type to {control_type}."}

@router.put('/change-token',
    responses={
        200: {
            "description": "Successful Response",
            "content": {"application/json":{"example": {"detail": "Successfully change the user token."}}}
        },
        404: {
            "description": "Setting not found",
            "content": {"application/json": {"example": {"detail": "Setting not found!"}}}
        },
    }
)
async def change_setting_token(
    request: Request,
    setting_user: SettingUserChangeToken,
    authorize: AuthJWT = Depends()
):
    authorize.jwt_required()

    user_id = int(authorize.get_jwt_subject())
    if user := await UserFetch.filter_by_id(user_id):
        user_token = await SettingUserFetch.filter_by_user_id(user['id'])

        if not user_token:
            raise HTTPException(status_code=404,detail="Setting not found!")

        authorize.get_raw_jwt(setting_user.token)

        # revoke token user before
        jti = authorize.get_raw_jwt(user_token['token'])['jti']
        request.app.state.redis.set(jti,'true')

        await SettingUserCrud.update_setting_user(user['id'],**setting_user.dict())
        return {"detail": "Successfully change the user token."}

@router.put('/change-settings',
    responses={
        200: {
            "description": "Successful Response",
            "content": {"application/json":{"example": {"detail": "Successfully update the control setting."}}}
        },
        404: {
            "description": "Setting not found",
            "content": {"application/json": {"example": {"detail": "Setting not found!"}}}
        },
    }
)
async def change_settings(setting_user: SettingUserUpdate, authorize: AuthJWT = Depends()):
    authorize.jwt_required()

    user_id = int(authorize.get_jwt_subject())
    if user := await UserFetch.filter_by_id(user_id):
        if not await SettingUserFetch.filter_by_user_id(user['id']):
            raise HTTPException(status_code=404,detail="Setting not found!")

        await SettingUserCrud.update_setting_user(user['id'],**setting_user.dict())
        return {"detail": "Successfully update the control setting."}

@router.put('/change-servo',
    responses={
        200: {
            "description": "Successful Response",
            "content": {"application/json":{"example": {"detail": "Successfully update the servo setting."}}}
        },
        404: {
            "description": "Setting not found",
            "content": {"application/json": {"example": {"detail": "Setting not found!"}}}
        },
    }
)
async def change_servo(setting_user: SettingUserUpdateServo, authorize: AuthJWT = Depends()):
    authorize.jwt_required()

    user_id = int(authorize.get_jwt_subject())
    if user := await UserFetch.filter_by_id(user_id):
        if not await SettingUserFetch.filter_by_user_id(user['id']):
            raise HTTPException(status_code=404,detail="Setting not found!")

        await SettingUserCrud.update_setting_user(user['id'],**setting_user.dict())
        return {"detail": "Successfully update the servo setting."}

@router.put('/change-plants/{plant_id}',
    responses={
        200: {
            "description": "Successful Response",
            "content": {"application/json":{"example": {"detail": "Successfully change the user plants."}}}
        },
        400: {
            "description": "Other plants still ongoing",
            "content": {"application/json": {"example": {"detail": "Upss, you have other plants still ongoing."}}}
        },
        404: {
            "description": "Setting & Plants not found",
            "content": {"application/json": {"example": {"detail": "string"}}}
        },
    }
)
async def change_setting_plants(plant_id: int = Path(...,gt=0), authorize: AuthJWT = Depends()):
    authorize.jwt_required()

    user_id = int(authorize.get_jwt_subject())
    if user := await UserFetch.filter_by_id(user_id):
        setting_user = await SettingUserFetch.filter_by_user_id(user['id'])

        if not setting_user:
            raise HTTPException(status_code=404,detail="Setting not found!")

        if not await PlantFetch.filter_by_id(plant_id):
            raise HTTPException(status_code=404,detail="Plants not found!")

        if setting_user['planted'] is True:
            raise HTTPException(status_code=400,detail="Upss, you have other plants still ongoing.")

        await SettingUserCrud.update_setting_user(user['id'],plant_id=plant_id)
        return {"detail": "Successfully change the user plants."}

@router.put('/change-plants-status',
    responses={
        200: {
            "description": "Successful Response",
            "content": {"application/json":{"example": {"detail": "Successfully change the planted to {planted}."}}}
        },
        404: {
            "description": "Setting not found",
            "content": {"application/json": {"example": {"detail": "Setting not found!"}}}
        },
    }
)
async def change_setting_plants_status(authorize: AuthJWT = Depends()):
    authorize.jwt_required()

    user_id = int(authorize.get_jwt_subject())
    if user := await UserFetch.filter_by_id(user_id):
        setting_user = await SettingUserFetch.filter_by_user_id(user['id'])

        if not setting_user:
            raise HTTPException(status_code=404,detail="Setting not found!")

        planted = not setting_user['planted']

        # planted False delete reset all report
        if planted is False:
            await ReportCrud.delete_report(user['id'])
            await GrowthPlantCrud.delete_growth_plant(user['id'])
            await AlertCrud.delete_alert(user['id'])
            # delete folder in growth plant
            MagicImage.delete_folder(name_folder=str(user['id']),path_delete='camera_module/')
            MagicImage.delete_folder(name_folder=str(user['id']),path_delete='camera_module_output/')
        else:
            # create alert when plants planted
            plants = await PlantFetch.filter_by_id(setting_user['plant_id'])
            await AlertCrud.create_alert(**{
                'type': 'already_planted',
                'message': f"Yeay, you successfully planted {plants['name']}",
                'user_id': user['id']
            })

        await SettingUserCrud.change_setting_plants_status(user['id'],planted)
        return {"detail": f"Successfully change the planted to {planted}."}
