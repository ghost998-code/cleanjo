import argparse
import asyncio
import secrets
from getpass import getpass

from sqlalchemy import or_, select

from app.core.constants import UserRole
from app.core.database import async_session_maker
from app.core.security import get_password_hash
from app.models import User
from app.services.otp import normalize_phone


def build_phone_email(phone: str) -> str:
    digits = "".join(char for char in phone if char.isdigit())
    return f"admin-{digits}@phone.cleanjo.local"


def build_default_name(phone: str) -> str:
    digits = "".join(char for char in phone if char.isdigit())
    return f"Admin {digits[-4:] or '0000'}"


def prompt_value(value: str | None, label: str, *, secret: bool = False) -> str | None:
    if value is not None:
        return value

    prompt = f"{label}: "
    entered = getpass(prompt) if secret else input(prompt)
    entered = entered.strip()
    return entered or None


async def create_admin(args: argparse.Namespace) -> int:
    raw_phone = prompt_value(args.phone, "Phone number")
    if not raw_phone:
        raise SystemExit("Phone number is required")

    normalized_phone = normalize_phone(raw_phone)
    full_name = prompt_value(args.full_name, "Full name") or build_default_name(
        normalized_phone
    )
    email = prompt_value(args.email, "Email") or build_phone_email(normalized_phone)
    password = prompt_value(
        args.password, "Password (leave blank to auto-generate)", secret=True
    )

    generated_password = password or secrets.token_urlsafe(18)
    password_hash = get_password_hash(generated_password)

    async with async_session_maker() as session:
        result = await session.execute(
            select(User).where(or_(User.phone == normalized_phone, User.email == email))
        )
        matches = result.scalars().all()

        user = None
        if matches:
            user_ids = {match.id for match in matches}
            if len(user_ids) > 1:
                raise SystemExit(
                    "Conflicting users already exist for that phone/email. Resolve the duplicates before rerunning the command."
                )
            user = matches[0]

        if user is None:
            user = User(
                email=email,
                password_hash=password_hash,
                full_name=full_name,
                phone=normalized_phone,
                role=UserRole.ADMIN,
            )
            session.add(user)
            action = "created"
        else:
            user.email = email
            user.full_name = full_name
            user.phone = normalized_phone
            user.role = UserRole.ADMIN
            user.password_hash = password_hash
            action = "updated"

        await session.commit()
        await session.refresh(user)

    print(f"Admin account {action}.")
    print(f"ID: {user.id}")
    print(f"Name: {user.full_name}")
    print(f"Email: {user.email}")
    print(f"Phone: {user.phone}")
    if password:
        print("Password: [provided value saved]")
    else:
        print(f"Generated password: {generated_password}")
    print("Role: admin")
    print(
        "Login to the web admin dashboard with the phone number above and the OTP flow on /login."
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="CleanJO admin account utilities",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_admin_parser = subparsers.add_parser(
        "create-admin",
        help="Create or update an admin account",
    )
    create_admin_parser.add_argument("--phone", help="Phone number used for OTP login")
    create_admin_parser.add_argument("--full-name", help="Admin display name")
    create_admin_parser.add_argument("--email", help="Admin email address")
    create_admin_parser.add_argument(
        "--password", help="Optional password for /api/auth/login"
    )
    create_admin_parser.set_defaults(handler=create_admin)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return asyncio.run(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
