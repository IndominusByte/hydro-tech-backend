from fastapi import APIRouter, Depends, Request, UploadFile
from fastapi_jwt_auth import AuthJWT
from controllers.UserController import UserFetch
from controllers.GrowthPlantController import GrowthPlantCrud, GrowthPlantFetch
from controllers.SettingUserController import SettingUserFetch
from schemas.growth_plants.GrowthPlantSchema import GrowthPlantImageData
from libs.MagicImage import MagicImage, SingleImageRequired
from libs.PlantCV import PlantCV

router = APIRouter()

# dependencies injection for validation an image
single_image_required = SingleImageRequired(
    max_file_size=4,
    allow_file_ext=['jpg','png','jpeg']
)

@router.post('/upload-image-camera',status_code=201,
    responses={
        201: {
            "description": "Successful Response",
            "content": {"application/json":{"example": {"detail": "Successfully upload image."}}}
        },
    }
)
async def upload_image_camera(
    request: Request,
    image: UploadFile = Depends(single_image_required),
    authorize: AuthJWT = Depends()
):
    authorize.jwt_required()

    user_id = int(authorize.get_jwt_subject())
    if user := await UserFetch.filter_by_id(user_id):
        # save image products to storage
        image_magic_camera = MagicImage(
            file=image.file,
            width=640,
            height=480,
            path_upload='camera_module/',
            dir_name=str(user['id'])
        )
        image_magic_camera.save_image()

        plant_height = PlantCV.measure_plants(image_magic_camera.file_name, str(user['id']))

        setting_user = await SettingUserFetch.filter_by_user_id(user['id'])
        camera_cal = request.app.state.redis.get(f"camera_cal:{user['id']}")

        data = dict()

        if (
            (camera_cal is None or camera_cal == 'false') and
            (setting_user is not None and setting_user['planted'] is True)
        ):
            data.update(**{'height': plant_height, 'image': image_magic_camera.file_name, 'user_id': user['id']})
        else:
            data.update(**{'height': 0, 'image': image_magic_camera.file_name, 'user_id': user['id']})

        await GrowthPlantCrud.create_growth_plant(**data)
        return {"detail": "Successfully upload image."}

@router.get('/recent-plant-image',response_model=GrowthPlantImageData)
async def recent_plant_image(authorize: AuthJWT = Depends()):
    authorize.jwt_required()

    user_id = int(authorize.get_jwt_subject())
    if user := await UserFetch.filter_by_id(user_id):
        return await GrowthPlantFetch.get_recent_plant_image(user['id'])
