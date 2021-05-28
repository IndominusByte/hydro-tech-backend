from pydantic import BaseModel, constr, conint

class DocumentationSchema(BaseModel):
    class Config:
        min_anystr_length = 1
        anystr_strip_whitespace = True

class DocumentationCreateUpdate(DocumentationSchema):
    title: constr(strict=True, min_length=3, max_length=100)
    description: constr(strict=True, min_length=20)
    category_doc_id: conint(strict=True, gt=0)

class DocumentationData(DocumentationSchema):
    documentations_id: int
    documentations_title: str
    documentations_slug: str
    documentations_description: str
    category_docs_id: int
    category_docs_name: str

class DocumentationSearchByName(DocumentationSchema):
    documentations_id: int
    documentations_title: str
    documentations_slug: str
    category_docs_id: int
    category_docs_name: str
