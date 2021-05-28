from sqlalchemy import Table, Column, Integer, BigInteger, String, Text, Float, DateTime, func
from config import metadata

plant = Table('plants', metadata,
    Column('id', BigInteger, primary_key=True),
    Column('name', String(100), unique=True, index=True, nullable=False),
    Column('image', String(100), nullable=False),
    Column('desc', Text, nullable=False),
    Column('ph_min', Float, nullable=False),
    Column('ph_max', Float, nullable=False),
    Column('tds_min', Float, nullable=False),
    Column('growth_value', Integer, nullable=False),
    Column('growth_type', String(20), nullable=False),
    Column('difficulty_level', String(20), nullable=False),
    Column('created_at', DateTime, default=func.now()),
    Column('updated_at', DateTime, default=func.now()),
)
