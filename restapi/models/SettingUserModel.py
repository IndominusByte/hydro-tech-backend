from sqlalchemy import (
    Table, Column, Integer, BigInteger, Text,
    Float, Boolean, DateTime, ForeignKey, func
)
from sqlalchemy.sql import expression, text
from config import metadata

setting_user = Table('setting_users', metadata,
    Column('id', BigInteger, primary_key=True),
    Column('camera', Boolean, nullable=False),
    Column('control_type', Boolean, server_default=expression.true()),
    Column('token', Text, nullable=False),
    Column('ph_max', Float, server_default=text("0")),
    Column('ph_min', Float, server_default=text("0")),
    Column('tds_min', Float, server_default=text("0")),
    Column('ph_cal', Float, server_default=text("0")),
    Column('tds_cal', Float, server_default=text("0")),
    Column('tank_height', Integer, server_default=text("0")),
    Column('tank_min', Integer, server_default=text("0")),
    Column('servo_horizontal', Integer, server_default=text("90")),
    Column('servo_vertical', Integer, server_default=text("90")),
    Column('planted', Boolean, server_default=expression.false()),
    Column('user_id', BigInteger, ForeignKey('users.id',onupdate='cascade',ondelete='cascade'), nullable=False),
    Column('plant_id', Integer, ForeignKey('plants.id',onupdate='cascade',ondelete='cascade'), nullable=False),
    Column('created_at', DateTime, default=func.now()),
    Column('planted_at', DateTime, default=func.now()),
)
