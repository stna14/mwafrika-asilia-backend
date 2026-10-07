from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. Import feature models here as they are built."""
    from app.features.admin_auth import models as _admin_auth_models  # noqa: F401
    from app.features.cms import models as _cms_models  # noqa: F401
    from app.features.newsroom import models as _newsroom_models  # noqa: F401


    Base.metadata.create_all(bind=engine)