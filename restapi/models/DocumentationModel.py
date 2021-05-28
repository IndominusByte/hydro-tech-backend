from sqlalchemy import Table, Column, Integer, String, Text, ForeignKey
from config import metadata

documentation = Table('documentations', metadata,
    Column('id', Integer, primary_key=True),
    Column('title', String(100), unique=True, index=True, nullable=False),
    Column('slug', Text, unique=True, index=True, nullable=False),
    Column('description', Text, nullable=False),
    Column('category_doc_id', Integer, ForeignKey('category_docs.id',onupdate='cascade',ondelete='cascade'), nullable=False),
)
