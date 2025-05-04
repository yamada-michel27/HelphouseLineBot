from datetime import datetime
from typing import Optional
from sqlmodel import Column, DateTime, SQLModel, Field, func

class User(SQLModel, table=True):
    id: str = Field(primary_key=True)

class Group(SQLModel, table=True):
    id: str = Field(primary_key=True)

class GarbageLog(SQLModel, table=True):
    id: str = Field(primary_key=True)
    user_id: str = Field(foreign_key="user.id")
    group_id: str = Field(foreign_key="group.id")
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False
        )
    )
