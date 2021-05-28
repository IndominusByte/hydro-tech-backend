from fastapi import APIRouter, Query, Depends
from fastapi_jwt_auth import AuthJWT
from controllers.ReportController import ReportFetch
from controllers.GrowthPlantController import GrowthPlantFetch
from controllers.UserController import UserFetch
from controllers.AlertController import AlertFetch
from schemas.reports.ReportSchema import ReportData, ReportChartData, ReportAlertData
from typing import Literal, List

router = APIRouter()

@router.get('/all-reports',response_model=List[ReportData])
async def get_all_reports(
    order_by: Literal['today','7day','30day','90day'] = Query(...),
    authorize: AuthJWT = Depends()
):
    authorize.jwt_required()

    user_id = int(authorize.get_jwt_subject())
    if user := await UserFetch.filter_by_id(user_id):
        return await ReportFetch.get_all_reports(user['id'],order_by)

@router.get('/ph-chart-report',response_model=List[ReportChartData])
async def ph_chart_report(order_by: Literal['7day','30day'] = Query(...), authorize: AuthJWT = Depends()):
    authorize.jwt_required()

    user_id = int(authorize.get_jwt_subject())
    if user := await UserFetch.filter_by_id(user_id):
        return await ReportFetch.get_chart_reports(user['id'],order_by,'ph')

@router.get('/tds-chart-report',response_model=List[ReportChartData])
async def tds_chart_report(order_by: Literal['7day','30day'] = Query(...), authorize: AuthJWT = Depends()):
    authorize.jwt_required()

    user_id = int(authorize.get_jwt_subject())
    if user := await UserFetch.filter_by_id(user_id):
        return await ReportFetch.get_chart_reports(user['id'],order_by,'tds')

@router.get('/growth-plant-chart-report',response_model=List[ReportChartData])
async def growth_plant_chart_report(order_by: Literal['7day','30day'] = Query(...), authorize: AuthJWT = Depends()):
    authorize.jwt_required()

    user_id = int(authorize.get_jwt_subject())
    if user := await UserFetch.filter_by_id(user_id):
        return await GrowthPlantFetch.get_growth_plant_chart_report(user['id'],order_by)

@router.get('/alert-report',response_model=List[ReportAlertData])
async def alert_report(order_by: Literal['today','3day','7day'] = Query(...), authorize: AuthJWT = Depends()):
    authorize.jwt_required()

    user_id = int(authorize.get_jwt_subject())
    if user := await UserFetch.filter_by_id(user_id):
        return await AlertFetch.get_alert_report(user['id'],order_by)
