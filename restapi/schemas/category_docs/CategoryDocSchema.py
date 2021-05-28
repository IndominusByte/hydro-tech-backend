from pydantic import BaseModel, constr

class CategoryDocSchema(BaseModel):
    class Config:
        min_anystr_length = 1
        anystr_strip_whitespace = True

class CategoryDocCreateUpdate(CategoryDocSchema):
    name: constr(strict=True, min_length=3, max_length=100)

class CategoryDocData(CategoryDocSchema):
    category_docs_id: int
    category_docs_name: str
