from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ---------- Session ----------

class SessionCreateRequest(BaseModel):
    clientId: str = Field(min_length=1, max_length=128)


class SessionResponse(BaseModel):
    success: bool
    voterId: str
    sessionToken: str
    expiresAt: str | None = None


# ---------- Candidate / Category ----------

class CandidateOut(BaseModel):
    id: str
    name: str
    role: str
    image: str
    about: str
    experience: str
    goals: str


class CategoryOut(BaseModel):
    id: str
    title: str
    description: str
    candidates: list[CandidateOut]


class CategoriesResponse(BaseModel):
    categories: list[CategoryOut]


# ---------- Vote submit ----------

class SubmitVoteRequest(BaseModel):
    categoryId: str
    candidateId: str


class SubmitVoteResponse(BaseModel):
    success: bool
    voteId: str | None = None
    message: str
    code: str | None = None


# ---------- Voting status ----------

class CategoryVoteStatus(BaseModel):
    voted: bool
    candidateId: str | None = None
    voteId: str | None = None
    status: str  # ACTIVE / LOCKED
    canVoteAgain: bool = False
    accessStatus: str | None = None  # LOCKED / UNLOCKED


class VotingStatusResponse(BaseModel):
    categories: dict[str, CategoryVoteStatus]


# ---------- Category access ----------

class CategoryAccessOut(BaseModel):
    voterId: str
    categoryId: str
    status: str
    unlockedAt: str | None = None
    unlockTransactionId: str | None = None


# ---------- Audit event ----------

class AuditEventOut(BaseModel):
    eventId: str
    eventType: str
    timestamp: str
    relatedEntity: str
    anonymousVoterReference: str
    metadata: dict = Field(default_factory=dict)