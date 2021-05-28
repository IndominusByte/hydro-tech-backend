from sqlalchemy import Table, Column, String, BigInteger, DateTime, ForeignKey, func
from config import metadata

alert = Table('alerts', metadata,
    Column('id', BigInteger, primary_key=True),
    Column('type', String(100), nullable=False),
    Column('message', String(100), nullable=False),
    Column('user_id', BigInteger, ForeignKey('users.id',onupdate='cascade',ondelete='cascade'), nullable=False),
    Column('created_at', DateTime, default=func.now()),
)
