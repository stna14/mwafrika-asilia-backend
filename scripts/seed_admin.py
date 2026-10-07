"""Create the first admin user.

Interactive:
    python -m scripts.seed_admin

Non-interactive (CI/CD, Docker):
    python -m scripts.seed_admin \
        --full-name "Jane Doe" \
        --email jane@example.com \
        --password "Str0ngPass" \
        --phone "+255..."

Or via env vars:
    ADMIN_FULL_NAME, ADMIN_EMAIL, ADMIN_PASSWORD, ADMIN_PHONE
"""
import argparse
import getpass
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import HTTPException  # noqa: E402
from pydantic import ValidationError  # noqa: E402
from sqlalchemy import inspect  # noqa: E402

from app.core.database import SessionLocal, engine  # noqa: E402
from app.features.admin_auth import service  # noqa: E402
from app.features.admin_auth.schemas import AdminCreate  # noqa: E402


def _require_tables() -> None:
    """Fail fast if tables are missing. Run the server once first."""
    inspector = inspect(engine)
    if "admin_users" not in inspector.get_table_names():
        print("ERROR: Table 'admin_users' does not exist.")
        print("Start the server once (uvicorn app.main:app) so tables are created,")
        print("then re-run this script.")
        sys.exit(1)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create an admin user.")
    parser.add_argument("--full-name", default=os.getenv("ADMIN_FULL_NAME"))
    parser.add_argument("--email", default=os.getenv("ADMIN_EMAIL"))
    parser.add_argument("--password", default=os.getenv("ADMIN_PASSWORD"))
    parser.add_argument("--phone", default=os.getenv("ADMIN_PHONE"))
    return parser.parse_args()


def _prompt_if_missing(args: argparse.Namespace) -> dict:
    full_name = args.full_name or input("Full name: ").strip()
    email = args.email or input("Email: ").strip()
    phone = args.phone
    if phone is None and sys.stdin.isatty():
        phone = input("Phone (optional): ").strip() or None

    password = args.password
    if not password:
        if not sys.stdin.isatty():
            print("ERROR: --password required in non-interactive mode.")
            sys.exit(1)
        password = getpass.getpass("Password: ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("ERROR: Passwords do not match.")
            sys.exit(1)

    return {
        "full_name": full_name,
        "email": email,
        "phone": phone,
        "password": password,
    }


def main() -> None:
    args = _parse_args()
    _require_tables()

    data = _prompt_if_missing(args)

    # Validate before touching the DB
    try:
        validated = AdminCreate(**data)
    except ValidationError as e:
        print("Invalid input:")
        for err in e.errors():
            loc = ".".join(str(x) for x in err["loc"])
            print(f"  - {loc}: {err['msg']}")
        sys.exit(1)

    db = SessionLocal()
    try:
        admin = service.create_admin(
            db,
            full_name=validated.full_name,
            email=validated.email,
            password=validated.password,
            phone=validated.phone,
        )
        print(f"\n✓ Admin created: {admin.email} (id={admin.id})")
    except HTTPException as e:
        print(f"ERROR: {e.detail}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()