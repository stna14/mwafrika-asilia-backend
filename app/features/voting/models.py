from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class VoterSession(Base):
    __tablename__ = "voter_sessions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    session_token: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    client_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE", index=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class VoteTransaction(Base):
    __tablename__ = "vote_transactions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)

    voter_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("voter_sessions.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    edition_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("wisac_editions.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    category_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("wisac_categories.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    nominee_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("wisac_nominees.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    vote_type: Mapped[str] = mapped_column(String(10), nullable=False, index=True)  # free / paid
    vote_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    vote_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="CONFIRMED", index=True
    )

    amount: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    payment_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)

    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)


class FreeVoteUsed(Base):
    __tablename__ = "free_votes_used"
    __table_args__ = (
        UniqueConstraint("voter_id", "category_id", name="uq_free_vote_voter_category"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    voter_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("voter_sessions.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    category_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("wisac_categories.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    vote_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("vote_transactions.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class VoteCategoryAccess(Base):
    __tablename__ = "vote_category_access"
    __table_args__ = (
        UniqueConstraint("voter_id", "category_id", name="uq_access_voter_category"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    voter_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("voter_sessions.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    category_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("wisac_categories.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="LOCKED", index=True)
    unlocked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    unlock_transaction_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class VoteAuditEvent(Base):
    __tablename__ = "vote_audit_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)

    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    voter_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("voter_sessions.id", ondelete="CASCADE"),
        nullable=True, index=True,
    )
    related_entity: Mapped[str | None] = mapped_column(String(64), nullable=True)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)