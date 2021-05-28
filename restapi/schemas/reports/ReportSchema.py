from pydantic import BaseModel, confloat, conint
from datetime import datetime
from typing import Literal

class ReportSchema(BaseModel):
    class Config:
        min_anystr_length = 1
        anystr_strip_whitespace = True

class ReportCreate(ReportSchema):
    ph: confloat(ge=0, le=1000000)
    tds: confloat(ge=0, le=1000000)
    temp: confloat(ge=0, le=1000000)
    ldr: Literal['bright','dark']
    tank: conint(ge=0, le=1000000)

class ReportData(ReportSchema):
    id: str
    ph: float
    tds: float
    temp: float
    ldr: Literal['bright','dark']
    tank: int
    created_at: datetime

class ReportAlertData(ReportSchema):
    id: str
    type: Literal['already_planted','ready_harvest','water_tank','water_temp']
    message: str
    user_id: str
    created_at: datetime

class ReportChartData(ReportSchema):
    avg: float
    date: str
