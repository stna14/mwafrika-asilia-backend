import secrets
import uuid
from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.features.voting.models import (
    FreeVoteUsed,
    VoteAuditEvent,
    VoteCategoryAccess,
    VoterSession,
    VoteTransaction,
)
from app.features.wisac.models import WisacCategory, WisacEdition, WisacNominee

SESSION_TTL_DAYS = 90


# ---------- Helpers ----------

def _new_public_id() -> str:
    return str(uuid.uuid4())


def _new_token() -> str:
    return secrets.token_urlsafe(48)


def _log_event(
    db: Session,
    *,
    event_type: str,
    voter_id: int | None,
    related_entity: str | None = None,
    metadata: dict | None = None,
) -> None:
    event = VoteAuditEvent(
        public_id=_new_public_id(),
        event_type=event_type,
        voter_id=voter_id,
        related_entity=related_entity,
        metadata_json=metadata or {},
    )
    db.add(event)


# ---------- Session ----------

def create_or_get_session(
    db: Session,
    *,
    client_id: str,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> VoterSession:
    existing = (
        db.query(VoterSession)
        .filter(VoterSession.client_id == client_id)
        .order_by(VoterSession.id.desc())
        .first()
    )

    if existing is not None and existing.status == "ACTIVE":
        existing.last_seen_at = datetime.utcnow()
        if ip_address:
            existing.ip_address = ip_address
        if user_agent:
            existing.user_agent = user_agent
        db.commit()
        db.refresh(existing)
        return existing

    now = datetime.utcnow()
    session = VoterSession(
        public_id=_new_public_id(),
        session_token=_new_token(),
        client_id=client_id,
        status="ACTIVE",
        ip_address=ip_address,
        user_agent=user_agent,
        created_at=now,
        last_seen_at=now,
        expires_at=now + timedelta(days=SESSION_TTL_DAYS),
    )
    db.add(session)
    db.flush()

    _log_event(
        db,
        event_type="ANONYMOUS_SESSION_CREATED",
        voter_id=session.id,
        related_entity=session.public_id,
        metadata={"ip": ip_address},
    )
    db.commit()
    db.refresh(session)
    return session


def get_voter_by_token(db: Session, token: str) -> VoterSession:
    session = (
        db.query(VoterSession)
        .filter(VoterSession.session_token == token)
        .first()
    )
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session token",
        )
    if session.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Session is not active",
        )
    if session.expires_at is not None and session.expires_at < datetime.utcnow():
        session.status = "EXPIRED"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired",
        )
    return session


# ---------- Category / Nominee ----------

def list_categories_with_candidates(db: Session) -> list[WisacCategory]:
    # Only categories with voting_status = open OR closed are relevant for
    # display. We return all categories for the current "active" editions
    # (status != 'completed') OR all editions — the frontend filters.
    return (
        db.query(WisacCategory)
        .order_by(WisacCategory.display_order.asc(), WisacCategory.name.asc())
        .all()
    )


def get_candidates_for_category(db: Session, category_id: int) -> list[WisacNominee]:
    category = db.query(WisacCategory).filter(WisacCategory.id == category_id).first()
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return (
        db.query(WisacNominee)
        .filter(WisacNominee.category_id == category_id)
        .filter(WisacNominee.status == "active")
        .order_by(WisacNominee.full_name.asc())
        .all()
    )


# ---------- Submit vote ----------

def submit_free_vote(
    db: Session,
    *,
    voter: VoterSession,
    category_id: int,
    nominee_id: int,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> VoteTransaction:
    # 1. Resolve category + nominee
    category = (
        db.query(WisacCategory).filter(WisacCategory.id == category_id).first()
    )
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "CATEGORY_NOT_FOUND", "message": "Category not found"},
        )

    nominee = (
        db.query(WisacNominee).filter(WisacNominee.id == nominee_id).first()
    )
    if nominee is None or nominee.category_id != category.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "CANDIDATE_NOT_FOUND", "message": "Candidate not found in this category"},
        )

    # 2. Check voting window
    if category.voting_status != "open":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "VOTING_CLOSED", "message": "Voting is not open for this category"},
        )

    edition = db.query(WisacEdition).filter(WisacEdition.id == category.edition_id).first()
    now = datetime.utcnow()
    if edition is not None:
        if edition.voting_start is not None and now < edition.voting_start:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "VOTING_NOT_STARTED", "message": "Voting has not started yet"},
            )
        if edition.voting_end is not None and now > edition.voting_end:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "VOTING_ENDED", "message": "Voting has ended for this edition"},
            )

    if nominee.status != "active":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "CANDIDATE_INACTIVE", "message": "This candidate is not accepting votes"},
        )

    # 3. Create vote transaction
    vote = VoteTransaction(
        public_id=_new_public_id(),
        voter_id=voter.id,
        edition_id=category.edition_id,
        category_id=category.id,
        nominee_id=nominee.id,
        vote_type="free",
        vote_number=1,
        vote_count=1,
        status="CONFIRMED",
        amount=None,
        payment_id=None,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(vote)
    db.flush()  # get vote.id

    # 4. Atomically record free-vote-used
    try:
        used = FreeVoteUsed(voter_id=voter.id, category_id=category.id, vote_id=vote.id)
        db.add(used)
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "FREE_VOTE_USED",
                "message": "You have already used your free vote in this category.",
            },
        )

    # 5. Increment nominee counters
    nominee.total_free_votes = (nominee.total_free_votes or 0) + 1
    nominee.total_votes = (nominee.total_votes or 0) + 1

    # 6. Log audit event
    _log_event(
        db,
        event_type="VOTE_CONFIRMED",
        voter_id=voter.id,
        related_entity=vote.public_id,
        metadata={
            "categoryId": str(category.id),
            "candidateId": str(nominee.id),
            "voteType": "free",
        },
    )

    voter.last_seen_at = datetime.utcnow()
    db.commit()
    db.refresh(vote)
    return vote


# ---------- Voting status ----------

def get_voting_status_for_voter(
    db: Session, voter: VoterSession
) -> dict[str, dict]:
    categories = db.query(WisacCategory).all()

    # Existing free votes by this voter
    votes = (
        db.query(VoteTransaction)
        .filter(VoteTransaction.voter_id == voter.id)
        .filter(VoteTransaction.status == "CONFIRMED")
        .all()
    )
    votes_by_cat: dict[int, VoteTransaction] = {v.category_id: v for v in votes}

    # Access entitlements
    access_rows = (
        db.query(VoteCategoryAccess)
        .filter(VoteCategoryAccess.voter_id == voter.id)
        .all()
    )
    access_by_cat: dict[int, VoteCategoryAccess] = {a.category_id: a for a in access_rows}

    result: dict[str, dict] = {}
    for cat in categories:
        v = votes_by_cat.get(cat.id)
        a = access_by_cat.get(cat.id)
        result[str(cat.id)] = {
            "voted": v is not None,
            "candidateId": str(v.nominee_id) if v else None,
            "voteId": v.public_id if v else None,
            "status": "ACTIVE" if cat.voting_status == "open" else "LOCKED",
            "canVoteAgain": False,  # paid revote comes in Phase D
            "accessStatus": a.status if a else None,
        }
    return result


# ---------- Category access ----------

def get_category_access(
    db: Session, voter: VoterSession, category_id: int
) -> VoteCategoryAccess | None:
    return (
        db.query(VoteCategoryAccess)
        .filter(VoteCategoryAccess.voter_id == voter.id)
        .filter(VoteCategoryAccess.category_id == category_id)
        .first()
    )


# ---------- Audit events ----------

def get_audit_events_for_voter(db: Session, voter: VoterSession) -> list[VoteAuditEvent]:
    return (
        db.query(VoteAuditEvent)
        .filter(VoteAuditEvent.voter_id == voter.id)
        .order_by(VoteAuditEvent.created_at.desc())
        .limit(200)
        .all()
    )