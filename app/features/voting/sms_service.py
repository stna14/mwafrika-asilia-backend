import uuid

import httpx

from app.core.config import settings


async def send_sms(phone_number: str, message: str) -> dict:
    """Send an SMS via SwalaSMS. Falls back to console print in mock mode.

    Returns:
        {"success": bool, "provider": str, "message": str, "raw": dict}
    """
    # Normalize: strip spaces, keep leading +
    phone = phone_number.replace(" ", "").strip()
    if phone.startswith("0"):
        phone = "+255" + phone[1:]
    elif phone.startswith("255") and not phone.startswith("+"):
        phone = "+" + phone

    if settings.SWALA_MOCK:
        print(f"\n[SMS MOCK] To: {phone}\n[SMS MOCK] Message: {message}\n")
        return {
            "success": True,
            "provider": "mock",
            "message": "SMS printed to console (mock mode)",
            "raw": {"to": phone, "message": message},
        }

    if not settings.SWALA_API_KEY:
        return {
            "success": False,
            "provider": "swalasms",
            "message": "SWALA_API_KEY not configured",
            "raw": {},
        }

    payload = {
        "sender_id": settings.SWALA_SENDER_ID,
        "recipient": phone,
        "body": message,
    }

    headers = {
        "Authorization": f"Bearer {settings.SWALA_API_KEY}",
        "Content-Type": "application/json",
        "Idempotency-Key": str(uuid.uuid4()),
        "Accept": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                settings.SWALA_API_URL,
                headers=headers,
                json=payload,
            )
        try:
            raw = resp.json()
        except Exception:
            raw = {"text": resp.text}

        if resp.status_code >= 400:
            return {
                "success": False,
                "provider": "swalasms",
                "message": f"HTTP {resp.status_code}: {raw}",
                "raw": raw,
            }

        return {
            "success": True,
            "provider": "swalasms",
            "message": "SMS queued for delivery",
            "raw": raw,
        }
    except Exception as e:
        return {
            "success": False,
            "provider": "swalasms",
            "message": f"Request failed: {e}",
            "raw": {},
        }
