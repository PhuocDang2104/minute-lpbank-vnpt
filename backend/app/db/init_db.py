from .session import engine
from .base import Base


def init_db() -> None:
    # Import models here so metadata is populated
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)