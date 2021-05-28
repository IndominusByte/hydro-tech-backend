from pydantic import BaseModel
from datetime import datetime
from typing import List, Literal, Optional

class PlantSchema(BaseModel):
    class Config:
        min_anystr_length = 1
        anystr_strip_whitespace = True

class PlantData(PlantSchema):
    plants_id: str
    plants_name: str
    plants_image: str
    plants_desc: str
    plants_ph_min: float
    plants_ph_max: float
    plants_tds_min: float
    plants_growth_value: int
    plants_growth_type: Literal['days','weeks']
    plants_difficulty_level: Literal['easy','medium','hard']
    plants_created_at: datetime
    plants_updated_at: datetime

class PlantPaginate(BaseModel):
    data: List[PlantData]
    total: int
    next_num: Optional[int]
    prev_num: Optional[int]
    page: int
    iter_pages: list
