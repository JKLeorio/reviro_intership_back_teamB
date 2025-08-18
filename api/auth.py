import contextlib
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi_users import FastAPIUsers, fastapi_users
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from api.permissions import require_roles
from models.group import Group
from models.user import User
from db.database import get_user_db, get_async_session
from schemas.user import AdminCreate, StudentRegister, StudentTeacherCreate, StudentTeacherRegister, StudentWithGroupResponse, UserCreate, UserRegister, UserResponse, AdminRegister
from fastapi_users.manager import BaseUserManager, IntegerIDMixin
from typing import Optional
from decouple import config
from fastapi_users.authentication import AuthenticationBackend, BearerTransport, JWTStrategy
from utils.password_utils import generate_password

SECRET = config('SECRET')

authRouter = APIRouter()

#lifetime временно равен 30 месяцам для тестировки
bearer_transport = BearerTransport(tokenUrl="auth/login")
auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=lambda: JWTStrategy(
        secret=SECRET, lifetime_seconds=3600 * 24 * 30),
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
current_super_user = fastapi_users.current_user(superuser=True)
current_admin_user = require_roles("admin")
current_teacher_user = require_roles("teacher", "admin")
current_student_user = require_roles("student", "teacher", "admin")
optional_current_user = fastapi_users.current_user(optional=True)

current_only_student_user = require_roles("student", "admin")

auth_router_full = fastapi_users.get_auth_router(auth_backend)
get_user_manager_context = contextlib.asynccontextmanager(get_user_manager)

for route in auth_router_full.routes:
    if route.path == "/login":
        authRouter.add_api_route(
            route.path,
            route.endpoint,
            methods=route.methods,
            name=route.name,
            description=
            """
            Get bearer auth token after authentication
            NOTE -> The email field a user is used as the username when logging in.
            """,
            response_model=route.response_model,
        )

# @router.post("/register", response_model=UserResponse)
# async def register(
#     user_data: UserRegister,
#     user_manager: UserManager = Depends(get_user_manager),
#     session: AsyncSession = Depends(get_async_session)
# ):
#     """Register a new user.
#     NOTE -> The email field when creating a user is used as the username when logging in.
#     """
#     if await session.scalar(select(User).where(User.email == user_data.email)):
#         raise HTTPException(status_code=400, detail="Email already registered")
#     user = await user_manager.create(UserCreate(**user_data.model_dump()))
#     return user


@authRouter.post("/register-admin",
                response_model=UserResponse, 
                status_code=status.HTTP_201_CREATED
                )
async def register_admin(
    user_data: AdminRegister,
    user_manager: UserManager = Depends(get_user_manager),
    session: AsyncSession = Depends(get_async_session),
    super_admin: User = Depends(current_super_user)
):
    """
    Register new admin, only for superadmin
    NOTE -> The email field when creating a user is used as the username when logging in.
    """
    if await session.scalar(select(User).where(
        User.email == user_data.email or User.phone_number == user_data.phone_number)):
        raise HTTPException(status_code=400, detail="Email or phone already registered")
    password = generate_password()
    user_data_dump = user_data.model_dump()
    user_data_dump['password'] = password
    
    user = await user_manager.create(AdminCreate(**user_data_dump))

    #Password sending logic here, for example sending into user email
    #smtp_server.send(message=f'here your password {password} for {url}')
    
    response = UserResponse.model_validate(user)
    response.password = password
    return response


@authRouter.post("/register-user", 
                 response_model=UserResponse,
                 status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: StudentTeacherRegister,
    user_manager: UserManager = Depends(get_user_manager),
    session: AsyncSession = Depends(get_async_session),
    admin: User = Depends(current_admin_user)
):
    """
    Register new user, only for admin
    NOTE -> The email field when creating a user is used as the username when logging in.
    """
    if await session.scalar(select(User).where(
        User.email == user_data.email or User.phone_number == user_data.phone_number)):
        raise HTTPException(status_code=400, detail="Email or phone already registered")
    password = generate_password()
    user_data_dump = user_data.model_dump()
    user_data_dump['password'] = password
    user = await user_manager.create(StudentTeacherCreate(**user_data_dump))

    #Password sending logic here, for example sending into user email
    #smtp_server.send(message=f'here your password {password} for {url}')

    response = UserResponse.model_validate(user)
    response.password = password
    return response


@authRouter.post(
    "/register-student-with-group/{group_id}",
    response_model=StudentWithGroupResponse,
    status_code=status.HTTP_201_CREATED
    )
async def register_student_with_group(
    group_id: int,
    user_data: StudentRegister,
    user_manager: UserManager = Depends(get_user_manager),
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_admin_user)
):
    group = await session.get(
        Group, 
        group_id, 
        options=[
            selectinload(Group.students)
            ]
        )
    if group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='group not found'
            )
    if await session.scalar(select(User).where(User.email == user_data.email)):
        raise HTTPException(status_code=400, detail="Email already registered")
    password = generate_password()
    user_data_dump = user_data.model_dump()
    user_data_dump['password'] = password
    new_user = await user_manager.create(StudentTeacherCreate(**user_data_dump))

    #Password sending logic here, for example sending into user email
    #smtp_server.send(message=f'here your password {password} for {url}')

    new_user = await session.merge(new_user)
    await session.refresh(new_user)
    await session.refresh(group, attribute_names=['students'])

    # if new_user not in (await group.awaitable_attrs.students):
    if new_user not in group.students:
        group.students.append(new_user)
    await session.commit()
    await session.refresh(new_user)

    return StudentWithGroupResponse(
        **(UserResponse.model_validate(new_user).model_dump()),
        group_id=group_id
    )