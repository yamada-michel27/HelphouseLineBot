import os
from sqlmodel import create_engine

engine = create_engine(
    os.getenv("DATABASE_URL"),
    echo=os.getenv("DEBUG", "false").lower() == "true",
    future=True,
)
