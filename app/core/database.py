from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

# 1. Tell SQLAlchemy to use the CA certificate ONLY when in production
connect_args = {}
if settings.APP_ENV == "production":
    connect_args = {"ssl": {"ca": "ca.pem"}}

# 2. Add connect_args to the engine
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
    connect_args=connect_args,
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
    from app.features.wisac import models as _wisac_models  # noqa: F401
    from app.features.voting import models as _voting_models  # noqa: F401
    from app.features.gallery import models as _gallery_models  # noqa: F401
    from app.features.ticketing import models as _ticketing_models  # noqa: F401
    from app.features.talent import models as _talent_models  # noqa: F401
    from app.features.media_library import models as _media_models  # noqa: F401
    from app.features.audit_logs import models as _audit_logs_models  # noqa: F401  <-- ADDED THIS

    Base.metadata.create_all(bind=engine)