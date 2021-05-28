from sqlalchemy import Table, Column, String, BigInteger, Float, DateTime, ForeignKey, func
from config import metadata

growth_plant = Table('growth_plants', metadata,
    Column('id', BigInteger, primary_key=True),
    Column('height', Float, nullable=False),
    Column('image', String(100), nullable=False),
    Column('user_id', BigInteger, ForeignKey('users.id',onupdate='cascade',ondelete='cascade'), nullable=False),
    Column('created_at', DateTime, default=func.now()),
)
