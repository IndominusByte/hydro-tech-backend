from fastapi import UploadFile, File, Form, Query, Depends
from libs.MagicImage import validate_single_upload_image
from typing import Optional, Literal

def upload_image_blog(image: UploadFile = File(...)):
    return validate_single_upload_image(
        image=image,
        allow_file_ext=['jpg','png','jpeg'],
        max_file_size=4
    )

def upload_image_blog_optional(image: Optional[UploadFile] = File(None)):
    if not image: return

    return validate_single_upload_image(
        image=image,
        allow_file_ext=['jpg','png','jpeg'],
        max_file_size=4
    )

def create_form_blog(
    title: str = Form(...,min_length=3,max_length=100),
    description: str = Form(...,min_length=20),
    image: upload_image_blog = Depends()
):
    return {
        "title": title,
        "description": description,
        "image": image
    }

def update_form_blog(
    title: str = Form(...,min_length=3,max_length=100),
    description: str = Form(...,min_length=20),
    image: upload_image_blog_optional = Depends()
):
    return {
        "title": title,
        "description": description,
        "image": image
    }

def get_all_query_blog(
    page: int = Query(...,gt=0),
    per_page: int = Query(...,gt=0),
    q: str = Query(None,min_length=1),
    order_by: Literal['newest','oldest','visitor'] = Query(...)
):
    return {
        "page": page,
        "per_page": per_page,
        "q": q,
        "order_by": order_by
    }
