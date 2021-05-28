from sqlalchemy import Table, Column, String, Integer, BigInteger, Text, DateTime, func
from sqlalchemy.sql import text
from config import metadata

blog = Table('blogs', metadata,
    Column('id', Integer, primary_key=True),
    Column('title', String(100), unique=True, index=True, nullable=False),
    Column('slug', Text, unique=True, index=True, nullable=False),
    Column('image', String(100), nullable=False),
    Column('description', Text, nullable=False),
    Column('visitor', BigInteger, server_default=text("0")),
    Column('created_at', DateTime, default=func.now()),
    Column('updated_at', DateTime, default=func.now()),
)
