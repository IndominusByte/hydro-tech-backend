from sqlalchemy import Table, Column, Integer, String
from config import metadata

category_doc = Table('category_docs', metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String(100), unique=True, index=True, nullable=False)
)
