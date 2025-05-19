from enum import Enum
from datetime import datetime
from typing import Optional
from sqlmodel import Column, DateTime, SQLModel, Field, func

class User(SQLModel, table=True):
    id: str = Field(primary_key=True)

class Group(SQLModel, table=True):
    id: str = Field(primary_key=True)

class TaskType(str, Enum):
    GARBAGE = "GARBAGE"
    DISHWASHING = "dishwashing"

class TaskLog(SQLModel, table=True):
    id: str = Field(primary_key=True)
    user_id: str = Field(foreign_key="user.id")
    group_id: str = Field(foreign_key="group.id")
    task_type: TaskType = Field(index=True)
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False
        )
    )
