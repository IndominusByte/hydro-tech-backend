from sqlalchemy import Table, Column, Integer, BigInteger, String, Float, DateTime, ForeignKey, func
from config import metadata

report = Table('reports', metadata,
    Column('id', BigInteger, primary_key=True),
    Column('ph', Float, nullable=False),
    Column('tds', Float, nullable=False),
    Column('temp', Float, nullable=False),
    Column('ldr', String(20), nullable=False),
    Column('tank', Integer, nullable=False),
    Column('user_id', BigInteger, ForeignKey('users.id',onupdate='cascade',ondelete='cascade'), nullable=False),
    Column('created_at', DateTime, default=func.now()),
)
