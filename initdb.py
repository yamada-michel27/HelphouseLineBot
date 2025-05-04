import os
from dotenv import load_dotenv
from sqlmodel import SQLModel, create_engine
import app.models

load_dotenv()

engine = create_engine(
    os.getenv("DATABASE_URL"),
    echo=True,
    future=True,
)

SQLModel.metadata.create_all(engine)
