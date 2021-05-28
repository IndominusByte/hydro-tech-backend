from pydantic import BaseModel, conint, confloat
from typing import Literal, Optional

class DashboardSchema(BaseModel):
    class Config:
        min_anystr_length = 1
        anystr_strip_whitespace = True

class DashboardSetValueServo(DashboardSchema):
    sh: conint(ge=0, le=180)
    sv: conint(ge=0, le=180)

class DashboardSetValueHydro(DashboardSchema):
    lamp: Optional[Literal['on','off']]
    phup: Optional[Literal['on','off']]
    phdown: Optional[Literal['on','off']]
    nutrition: Optional[Literal['on','off']]
    solenoid: Optional[Literal['on','off']]
    phmax: Optional[confloat(ge=0, le=1000000)]
    phmin: Optional[confloat(ge=0, le=1000000)]
    tdsmin: Optional[confloat(ge=0, le=1000000)]
    phcal: Optional[confloat(ge=0, le=1000000)]
    tdscal: Optional[confloat(ge=0, le=1000000)]
    tankheight: Optional[conint(ge=0, le=1000000)]
    tankmin: Optional[conint(ge=0, le=1000000)]

class DashboardHydroData(DashboardSchema):
    ph: confloat(ge=0, le=1000000)
    tds: confloat(ge=0, le=1000000)
    temp: confloat(ge=0, le=1000000)
    ldr: Literal['bright','dark']
    tank: conint(ge=0, le=1000000)
    lamp: Literal['on','off']
    phup: Literal['on','off']
    phdown: Literal['on','off']
    nutrition: Literal['on','off']
    solenoid: Literal['on','off']
