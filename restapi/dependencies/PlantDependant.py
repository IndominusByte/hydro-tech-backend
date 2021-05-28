from fastapi import UploadFile, File, Form, Query, Depends
from libs.MagicImage import validate_single_upload_image
from typing import Optional, Literal

def upload_image_plant(image: UploadFile = File(...)):
    return validate_single_upload_image(
        image=image,
        allow_file_ext=['jpg','png','jpeg'],
        max_file_size=4
    )

def upload_image_plant_optional(image: Optional[UploadFile] = File(None)):
    if not image: return

    return validate_single_upload_image(
        image=image,
        allow_file_ext=['jpg','png','jpeg'],
        max_file_size=4
    )

def create_form_plant(
    name: str = Form(...,min_length=3,max_length=100),
    desc: str = Form(...,min_length=20),
    ph_max: float = Form(...,gt=0,le=20),
    ph_min: float = Form(...,gt=0,le=20),
    tds_min: float = Form(...,gt=0,le=3000),
    growth_value: int = Form(...,gt=0),
    growth_type: Literal['days','weeks'] = Form(...),
    difficulty_level: Literal['easy','medium','hard'] = Form(...),
    image: upload_image_plant = Depends()
):
    return {
        "name": name,
        "desc": desc,
        "ph_max": ph_max,
        "ph_min": ph_min,
        "tds_min": tds_min,
        "growth_value": growth_value,
        "growth_type": growth_type,
        "difficulty_level": difficulty_level,
        "image": image
    }

def update_form_plant(
    name: str = Form(...,min_length=3,max_length=100),
    desc: str = Form(...,min_length=20),
    ph_max: float = Form(...,gt=0,le=20),
    ph_min: float = Form(...,gt=0,le=20),
    tds_min: float = Form(...,gt=0,le=3000),
    growth_value: int = Form(...,gt=0),
    growth_type: Literal['days','weeks'] = Form(...),
    difficulty_level: Literal['easy','medium','hard'] = Form(...),
    image: upload_image_plant_optional = Depends()
):
    return {
        "name": name,
        "desc": desc,
        "ph_max": ph_max,
        "ph_min": ph_min,
        "tds_min": tds_min,
        "growth_value": growth_value,
        "growth_type": growth_type,
        "difficulty_level": difficulty_level,
        "image": image
    }

def get_all_query_plant(
    page: int = Query(...,gt=0),
    per_page: int = Query(...,gt=0),
    q: str = Query(None,min_length=1),
    difficulty: Literal['easy','medium','hard'] = Query(None)
):
    return {
        "page": page,
        "per_page": per_page,
        "q": q,
        "difficulty": difficulty
    }
