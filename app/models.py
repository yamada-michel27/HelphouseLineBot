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

# class SampleCount(SQLModel, table=True):
#     user_id: str = Field(primary_key=True)
#     count: int = Field(default=0)
#     garbage_type: Optional[str] = Field(default=None)
#     created_at: datetime = Field(
#         sa_column=Column(
#             DateTime(timezone=True),
#             server_default=func.now(),
#             nullable=False
#         )
#     )
#     updated_at: datetime = Field(
#         sa_column=Column(
#             DateTime(timezone=True),
#             server_default=func.now(),
#             onupdate=func.now(),
#             nullable=False
#         )
#     )
