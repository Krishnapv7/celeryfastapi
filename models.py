from sqlalchemy import (
    Table,Column,Integer,String,Text,DateTime,ForeignKey,Float
)
from sqlalchemy.sql import func
from database import metadata

ReviewHistory = Table(
    "review_history",
    metadata,
    Column("id",Integer,primary_key=True,autoincrement=True),
    Column("text",String,nullable=True),
    Column("stars",Integer,nullable=False),
    Column("review_id",String(255),nullable=False),
    Column("tone",String(255),nullable=True),
    Column("sentiment",String(255),nullable=True),
    Column("category_id",Integer,ForeignKey("category.id"),nullable=False),
    Column("created_at",DateTime,default=func.now()),
    Column("updated_at",DateTime,default=func.now()),
)

Category = Table(
    "category",
    metadata,
    Column("id",Integer,primary_key=True,autoincrement=True),
    Column("name",String(255),unique=True,nullable=False),
    Column("description",Text,nullable=True),
)

AccessLog = Table(
    "access_log",
    metadata,
    Column("id",Integer,primary_key=True,autoincrement=True),
    Column("text",String(255),nullable=False),
    Column("created_at",DateTime,default=func.now()),
)