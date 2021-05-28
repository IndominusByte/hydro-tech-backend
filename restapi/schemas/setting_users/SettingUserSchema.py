from pydantic import BaseModel, constr, confloat, conint, validator, StrictBool
from datetime import datetime

class SettingUserSchema(BaseModel):
    class Config:
        min_anystr_length = 1
        anystr_strip_whitespace = True

class SettingUserCreate(SettingUserSchema):
    camera: StrictBool
    token: constr(strict=True, min_length=5)
    plant_id: constr(strict=True, regex=r'^[0-9]*$')

    @validator('plant_id')
    def parse_str_to_int(cls, v):
        return int(v) if v else None

class SettingUserChangeToken(SettingUserSchema):
    token: constr(strict=True, min_length=5)

class SettingUserUpdateServo(SettingUserSchema):
    servo_horizontal: conint(strict=True, ge=0, le=180)
    servo_vertical: conint(strict=True, ge=0, le=180)

class SettingUserUpdate(SettingUserSchema):
    ph_max: confloat(ge=0, le=20)
    ph_min: confloat(ge=0, le=20)
    tds_min: confloat(ge=0, le=3000)
    ph_cal: confloat(ge=0, le=10000)
    tds_cal: confloat(ge=0, le=10000)
    tank_height: conint(strict=True, ge=0, le=1000000)
    tank_min: conint(strict=True, ge=0, le=1000000)

class SettingUserPlantProgressData(SettingUserSchema):
    percentage: int

class SettingUserData(SettingUserSchema):
    setting_users_id: str
    setting_users_camera: bool
    setting_users_control_type: bool
    setting_users_token: str
    setting_users_ph_max: float
    setting_users_ph_min: float
    setting_users_tds_min: float
    setting_users_ph_cal: float
    setting_users_tds_cal: float
    setting_users_tank_height: int
    setting_users_tank_min: int
    setting_users_servo_horizontal: int
    setting_users_servo_vertical: int
    setting_users_planted: bool
    setting_users_created_at: datetime
    setting_users_planted_at: datetime
    plants_id: str
    plants_ph_max: float
    plants_ph_min: float
    plants_tds_min: float
