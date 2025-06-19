import asyncio
import argparse
import sys

from sqlalchemy import select

from db.database import get_async_session_context, get_user_db_context
from models.user import User
from db.schemas import SuperAdminCreate, SuperAdminUpdate
from api.auth import get_user_manager_context



async def create_superuser(email: str, password: str):
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

async def delete_superuser(email : str):
    async with get_async_session_context() as session:
        async with get_user_db_context(session=session) as user_db:
            if await session.scalar(select(User).where(User.email == email)):
                print(f'User with {email} email is already registered')
                exit()
            async with get_user_manager_context(user_db=user_db) as user_manager:
                user = await user_manager.get_by_email(user_email=email)
                await user_manager.delete(user=user)
                print(f"superuser succesfull deleted")


async def update_superuser_password(email : str, password : str):
    user_update = SuperAdminUpdate(email=email, password=password)
    async with get_async_session_context() as session:
        async with get_user_db_context(session=session) as user_db:
            if await session.scalar(select(User).where(User.email == email)):
                print(f'User with {email} email is already registered')
                exit()
            async with get_user_manager_context(user_db=user_db) as user_manager:
                user = await user_manager.get_by_email(user_email=email)
                await user_manager.update(user_update=user_update, user=user)
                print(f"Суперпользователь создан: {user.email}")


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    #createsuperuser
    csu = subparsers.add_parser("createsuperuser")
    csu.add_argument("--email", required=True)
    csu.add_argument("--password", required=True)

    dsu = subparsers.add_parser("deletesuperuser")
    dsu.add_argument("--user_email", required=True)

    usu = subparsers.add_parser("updatesuperuser")
    usu.add_argument("--user_email", required=True)
    usu.add_argument("--new_password", required=True)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "createsuperuser":
        asyncio.run(create_superuser(args.email, args.password))
    elif args.command == "updatesuperuser":
        asyncio.run(delete_superuser(args.user_email))
    elif args.command == "deletesuperuser":
        asyncio.run(update_superuser_password(args.user_email, args.new_password))

if __name__ == "__main__":
    main()