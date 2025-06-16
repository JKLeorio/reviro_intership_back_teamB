import asyncio
import argparse
import sys

from sqlalchemy import select

from db.database import get_async_session_context, get_user_db_context
from db.models import User
from db.schemas import SuperAdminCreate
from api.auth import get_user_manager_context



async def createsuperuser(email: str, password: str):
    async with get_async_session_context() as session:
        async with get_user_db_context(session=session) as user_db:
            if await session.scalar(select(User).where(User.email == email)):
                print(f'User with {email} email is already registered')
                exit()
            async with get_user_manager_context(user_db=user_db) as user_manager:
                user = await user_manager.create(
                    SuperAdminCreate(
                    email=email,
                    password=password
                    )
                )
                print(f"Суперпользователь создан: {user.email}")


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    #createsuperuser
    csu = subparsers.add_parser("createsuperuser")

    csu.add_argument("--email", required=True)
    csu.add_argument("--password", required=True)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "createsuperuser":
        asyncio.run(createsuperuser(args.email, args.password))

if __name__ == "__main__":
    main()