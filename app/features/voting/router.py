from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.features.voting import service
from app.features.voting.schemas import (
    AuditEventOut,
    CandidateOut,
    CategoriesResponse,
    CategoryAccessOut,
    CategoryOut,
    SessionCreateRequest,
    SessionResponse,
    SubmitVoteRequest,
    SubmitVoteResponse,
    VotingStatusResponse,
)
from app.features.wisac.models import WisacNominee

router = APIRouter(prefix="/api/votes", tags=["voting"])


def _to_candidate(n: WisacNominee) -> CandidateOut:
    return CandidateOut(
        id=str(n.id),
        name=n.stage_name or n.full_name,
        role=n.profession or "",
        image=n.profile_image_url or "",
        about=n.biography or "",
        experience=n.experience or "",
        goals=n.goals or "",
    )


def _require_token(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )
    return authorization.split(" ", 1)[1].strip()


# ---------- Session ----------

@router.post("/session", response_model=SessionResponse)
def create_session(
    payload: SessionCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    voter = service.create_or_get_session(
        db, client_id=payload.clientId, ip_address=ip, user_agent=ua
    )
    return SessionResponse(
        success=True,
        voterId=voter.public_id,
        sessionToken=voter.session_token,
        expiresAt=voter.expires_at.isoformat() if voter.expires_at else None,
    )


@router.get("/session")
def get_session(
    token: str = Depends(_require_token),
    db: Session = Depends(get_db),
):
    voter = service.get_voter_by_token(db, token)
    return {
        "success": True,
        "voterId": voter.public_id,
        "sessionToken": voter.session_token,
        "expiresAt": voter.expires_at.isoformat() if voter.expires_at else None,
    }


# ---------- Categories ----------

@router.get("/categories", response_model=CategoriesResponse)
def list_categories(db: Session = Depends(get_db)):
    categories = service.list_categories_with_candidates(db)
    return CategoriesResponse(
        categories=[
            CategoryOut(
                id=str(c.id),
                title=c.name,
                description=c.description or "",
                candidates=[
                    _to_candidate(n)
                    for n in service.get_candidates_for_category(db, c.id)
                ],
            )
            for c in categories
        ]
    )


@router.get("/categories/{category_id}/candidates")
def list_candidates_for_category(category_id: int, db: Session = Depends(get_db)):
    nominees = service.get_candidates_for_category(db, category_id)
    return {"candidates": [_to_candidate(n) for n in nominees]}


# ---------- Submit vote ----------

@router.post("/submit", response_model=SubmitVoteResponse)
def submit_vote(
    payload: SubmitVoteRequest,
    request: Request,
    token: str = Depends(_require_token),
    db: Session = Depends(get_db),
):
    voter = service.get_voter_by_token(db, token)
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")

    try:
        category_id = int(payload.categoryId)
        nominee_id = int(payload.candidateId)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_ID", "message": "categoryId and candidateId must be numeric"},
        )

    vote = service.submit_free_vote(
        db,
        voter=voter,
        category_id=category_id,
        nominee_id=nominee_id,
        ip_address=ip,
        user_agent=ua,
    )
    return SubmitVoteResponse(
        success=True,
        voteId=vote.public_id,
        message="Your vote has been recorded.",
    )


# ---------- Status ----------

@router.get("/status", response_model=VotingStatusResponse)
def voting_status(
    token: str = Depends(_require_token),
    db: Session = Depends(get_db),
):
    voter = service.get_voter_by_token(db, token)
    categories = service.get_voting_status_for_voter(db, voter)
    return VotingStatusResponse(categories=categories)


# ---------- Category access ----------

@router.get("/categories/{category_id}/access", response_model=CategoryAccessOut | None)
def category_access(
    category_id: int,
    token: str = Depends(_require_token),
    db: Session = Depends(get_db),
):
    voter = service.get_voter_by_token(db, token)
    access = service.get_category_access(db, voter, category_id)
    if access is None:
        return None
    return CategoryAccessOut(
        voterId=voter.public_id,
        categoryId=str(access.category_id),
        status=access.status,
        unlockedAt=access.unlocked_at.isoformat() if access.unlocked_at else None,
        unlockTransactionId=str(access.unlock_transaction_id) if access.unlock_transaction_id else None,
    )


# ---------- Audit events ----------

@router.get("/audit", response_model=list[AuditEventOut])
def audit_events(
    token: str = Depends(_require_token),
    db: Session = Depends(get_db),
):
    voter = service.get_voter_by_token(db, token)
    events = service.get_audit_events_for_voter(db, voter)
    return [
        AuditEventOut(
            eventId=e.public_id,
            eventType=e.event_type,
            timestamp=e.created_at.isoformat(),
            relatedEntity=e.related_entity or "",
            anonymousVoterReference=voter.public_id,
            metadata=e.metadata_json or {},
        )
        for e in events
    ]