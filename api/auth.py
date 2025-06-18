import contextlib
from fastapi import APIRouter, Depends, HTTPException
from fastapi_users import FastAPIUsers, fastapi_users
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from db.database import get_user_db, get_async_session
from db.schemas import UserCreate, UserRegister, UserResponse
from fastapi_users.manager import BaseUserManager, IntegerIDMixin
from fastapi import Request
from typing import Optional
from decouple import config
from fastapi_users.authentication import AuthenticationBackend, BearerTransport, JWTStrategy


SECRET = config('SECRET')

router = APIRouter()

bearer_transport = BearerTransport(tokenUrl="auth/login")
auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=lambda: JWTStrategy(
        secret=SECRET, lifetime_seconds=3600 * 24 * 7),
)


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self, user: User,
                                request: Optional[Request] = None):
        print(f"User {user.id} has registered.")

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        print(f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        print(f"Verification requested for user {user.id}. Verification token: {token}")


async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)

fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend]
)
current_user = fastapi_users.current_user()

router = fastapi_users.get_auth_router(auth_backend)
get_user_manager_context = contextlib.asynccontextmanager(get_user_manager)


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserRegister,
    user_manager: UserManager = Depends(get_user_manager),
    session: AsyncSession = Depends(get_async_session)
):
    """Register a new user.
    NOTE -> The email field when creating a user is used as the username when logging in.
    """
    if await session.scalar(select(User).where(User.email == user_data.email)):
        raise HTTPException(status_code=400, detail="Email already registered")
    user = await user_manager.create(UserCreate(**user_data.model_dump()))
    return user
