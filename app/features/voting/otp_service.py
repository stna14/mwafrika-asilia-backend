import secrets
import uuid
from datetime import datetime, timedelta

import bcrypt
from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.features.voting.models import PhoneVerification, VoterSession
from app.features.voting.sms_service import send_sms


def _new_public_id() -> str:
    return str(uuid.uuid4())


def _generate_otp() -> str:
    """6-digit code, always zero-padded."""
    return f"{secrets.randbelow(1_000_000):06d}"


def _hash_otp(code: str) -> str:
    return bcrypt.hashpw(code.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_otp(code: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(code.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def _normalize_phone(raw: str) -> str:
    """Accept 0712345678, 255712345678, +255712345678 — always return +255..."""
    p = raw.replace(" ", "").replace("-", "").strip()
    if p.startswith("0"):
        p = "+255" + p[1:]
    elif p.startswith("255") and not p.startswith("+"):
        p = "+" + p
    elif not p.startswith("+"):
        p = "+" + p

    # Basic Tanzania sanity
    digits = p[1:]
    if not (digits.isdigit() and 9 <= len(digits) <= 15):
        raise HTTPException(status_code=400, detail="Invalid phone number")
    return p


async def request_otp(
    db: Session,
    *,
    phone_number: str,
    voter: VoterSession | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> PhoneVerification:
    phone = _normalize_phone(phone_number)

    # Rate limit: max N requests per phone per hour
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    recent = (
        db.query(func.count(PhoneVerification.id))
        .filter(PhoneVerification.phone_number == phone)
        .filter(PhoneVerification.created_at >= one_hour_ago)
        .scalar()
        or 0
    )
    if recent >= settings.OTP_MAX_REQUESTS_PER_HOUR:
        raise HTTPException(
            status_code=429,
            detail={
                "code": "TOO_MANY_REQUESTS",
                "message": "Too many OTP requests for this phone. Try again later.",
            },
        )

    code = _generate_otp()
    record = PhoneVerification(
        public_id=_new_public_id(),
        phone_number=phone,
        otp_hash=_hash_otp(code),
        otp_expires_at=datetime.utcnow() + timedelta(minutes=settings.OTP_EXPIRY_MINUTES),
        status="pending",
        voter_id=voter.id if voter else None,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    message = (
        f"Your WISAC voting verification code is {code}. "
        f"Enter this code on the website to confirm your vote."
    )
    result = await send_sms(phone, message)
    if not result["success"]:
        record.status = "failed"
        db.commit()
        raise HTTPException(
            status_code=502,
            detail={
                "code": "SMS_FAILED",
                "message": result.get("message", "SMS provider failed"),
            },
        )

    return record


def verify_otp(
    db: Session,
    *,
    phone_number: str,
    code: str,
    voter: VoterSession | None = None,
) -> dict:
    phone = _normalize_phone(phone_number)

    record = (
        db.query(PhoneVerification)
        .filter(PhoneVerification.phone_number == phone)
        .filter(PhoneVerification.status == "pending")
        .order_by(PhoneVerification.id.desc())
        .first()
    )
    if record is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "NO_OTP", "message": "No pending verification for this phone"},
        )

    if record.otp_expires_at < datetime.utcnow():
        record.status = "expired"
        db.commit()
        raise HTTPException(
            status_code=410,
            detail={"code": "OTP_EXPIRED", "message": "The code has expired. Request a new one."},
        )

    if record.attempts >= settings.OTP_MAX_ATTEMPTS:
        record.status = "blocked"
        db.commit()
        raise HTTPException(
            status_code=429,
            detail={"code": "TOO_MANY_ATTEMPTS", "message": "Too many attempts. Request a new code."},
        )

    if not _verify_otp(code, record.otp_hash):
        record.attempts += 1
        db.commit()
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_OTP", "message": "Incorrect code"},
        )

    # Success
    record.status = "verified"
    record.verified_at = datetime.utcnow()
    if voter is not None:
        voter.verified_phone = phone
        voter.phone_verified_at = datetime.utcnow()
    db.commit()
    db.refresh(record)

    return {"success": True, "phone_number": phone, "verification_id": record.public_id}