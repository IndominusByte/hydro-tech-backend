from sqlalchemy import Table, Column, Text, BigInteger, DateTime, ForeignKey, func
from config import metadata

chat = Table('chats', metadata,
    Column('id', BigInteger, primary_key=True),
    Column('message', Text, nullable=False),
    Column('user_id', BigInteger, ForeignKey('users.id',onupdate='cascade',ondelete='cascade'), nullable=False),
    Column('created_at', DateTime, default=func.now()),
)
