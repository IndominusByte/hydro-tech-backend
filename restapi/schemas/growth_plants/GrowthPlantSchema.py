from pydantic import BaseModel

class GrowthPlantSchema(BaseModel):
    class Config:
        min_anystr_length = 1
        anystr_strip_whitespace = True

class GrowthPlantImageData(GrowthPlantSchema):
    image: str
