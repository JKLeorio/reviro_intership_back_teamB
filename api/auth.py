import contextlib
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from fastapi_users import FastAPIUsers, fastapi_users
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from api.permissions import require_roles
from db.types import OTP_purpose
from models.group import Group
from models.user import OTP, User
from db.database import get_user_db, get_async_session
from schemas.user import AdminCreate, PersonalDataUpdate, SendOtp, StudentRegister, StudentTeacherCreate, StudentTeacherRegister, TeacherRegister, TeacherWithGroupResponse, UserResponse, AdminRegister
from schemas.group import GroupShort, StudentWithGroupResponse
from fastapi_users.manager import BaseUserManager, IntegerIDMixin
from typing import Annotated, Any, List, Optional
from decouple import config
from fastapi_users.authentication import AuthenticationBackend, BearerTransport, JWTStrategy
from utils.date_time_utils import get_current_time
from utils.password_utils import generate_password
from utils.security import generate_otp6, hash_code

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



async def create_user(
    session: AsyncSession,
    user_manager: UserManager,
    user_data: BaseModel, 
    schema_cls: BaseModel
) -> list[User, str]:
    if await session.scalar(select(User).where(
        User.email == user_data.email or User.phone_number == user_data.phone_number)
        ):
        raise HTTPException(status_code=400, detail="Email or phone already registered")
    password = generate_password()
    user_data_dump = user_data.model_dump()
    user_data_dump['password'] = password
    
    new_user = await user_manager.create(schema_cls(**user_data_dump))
    return [new_user, password]


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

    new_user, password = await create_user(
        session=session,
        user_manager=user_manager,
        user_data=user_data,
        schema_cls=AdminCreate
        )
    
    response = UserResponse.model_validate(new_user)
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

    new_user, password = await create_user(
        session=session,
        user_manager=user_manager,
        user_data=user_data,
        schema_cls=StudentTeacherCreate
        )

    response = UserResponse.model_validate(new_user)
    response.password = password
    return response




async def register_user_with_group(
        group_id: int, 
        session: AsyncSession,
        user_manager: UserManager,
        user_data: BaseModel,
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
    
    new_user, password = await create_user(
        session=session,
        user_manager=user_manager,
        user_data=user_data,
        schema_cls=AdminCreate
        )
    
    await session.refresh(new_user)
    await session.refresh(group, attribute_names=['students'])

    # if new_user not in (await group.awaitable_attrs.students):
    if new_user not in group.students:
        group.students.append(new_user)
    await session.commit()
    await session.refresh(new_user)
    return {
        'user' : new_user,
        'group' : group
    }


@authRouter.post(
    "/register-student-with-group",
    response_model=StudentWithGroupResponse,
    status_code=status.HTTP_201_CREATED
    )
async def register_student_with_group(
    group_id: Annotated[List[int], Query()],
    user_data: StudentRegister,
    user_manager: UserManager = Depends(get_user_manager),
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_admin_user)
):
    group_ids = set(group_id)
    stmt = (
        select(Group)
        .where(
            Group.is_archived.is_(False),
            Group.id.in_(group_ids)
        )
    )
    result = await session.execute(stmt)
    groups = result.scalars().all()
    if len(group_ids) != len(groups):
        raise HTTPException(status_code=404, detail='group not found')
    
    new_user, password = await create_user(
        session=session,
        user_manager=user_manager,
        user_data=user_data,
        schema_cls=AdminCreate
        )
    
    new_user = await session.merge(new_user)

    groups = (await session.execute(
        stmt.options(
            selectinload(
                Group.students)
                )
            )
        ).scalars().all()
    for group in groups:
        group.students.append(new_user)

    await session.commit()
    await session.refresh(new_user, attribute_names=['groups_joined'])
    response_groups = [
        GroupShort.model_validate(
            group, 
            from_attributes=True
            ) for group in new_user.groups_joined
            ]

    return StudentWithGroupResponse(
        id=new_user.id,
        full_name=new_user.full_name,
        email=new_user.email,
        phone_number=new_user.phone_number,
        role=new_user.role,
        is_active=new_user.is_active,
        groups=response_groups
    )


@authRouter.post(
    "/register-teacher-with-group/{group_id}",
    response_model=TeacherWithGroupResponse,
    status_code=status.HTTP_201_CREATED
    )
async def register_teacher_with_group(
    group_id: int,
    user_data: TeacherRegister,
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
    
    new_user, password = await create_user(
        session=session,
        user_manager=user_manager,
        user_data=user_data,
        schema_cls=AdminCreate
        )

    new_user = await session.merge(new_user)
    await session.refresh(new_user)
    await session.refresh(group, attribute_names=['students', 'teacher'])

    group.teacher = new_user

    await session.commit()
    await session.refresh(new_user)

    return TeacherWithGroupResponse(
        id=new_user.id,
        full_name=new_user.first_name + " " + new_user.last_name,
        is_active=new_user.is_active,
        phone_number=new_user.phone_number,
        email=new_user.email,
        role=new_user.role,
        group_id=group_id,
        description=new_user.description
    )




async def generate_otp(
    user: User,
    purpose: OTP_purpose,
    session: AsyncSession
) -> str:
    
    otp_lifetime = timedelta(minutes=2)

    now = get_current_time()
    stmt = (
        select(OTP)
        .where(
            OTP.user_id == user.id,
            OTP.purpose == purpose,
            OTP.is_active.is_(True)
        )
        .with_for_update(skip_locked=True)
    )
    res = await session.execute(stmt)
    existing: OTP = res.scalar_one_or_none()

    if existing is not None:
        if existing.last_sent_at and existing.last_sent_at + timedelta(seconds=5) > now:
            raise ValueError("too frequent requests, try later")
        
        existing.is_active = False
        await session.flush()
    
    code = generate_otp6()
    hashed_code = hash_code(code=code)
    record = OTP(
        expires_at = now + otp_lifetime,
        consumed_at = None,
        purpose = purpose,
        code_hash = hashed_code,
        user_id = user.id,
        last_sent_at = now,
    )
    session.add(record)
    await session.commit()
    return code


async def verify_otp(
    session: AsyncSession,
    user: User,
    purpose: OTP_purpose,
    code: str
) -> bool:
    now = get_current_time()

    stmt = (
        select(OTP)
        .where(
            OTP.user_id == user.id,
            OTP.purpose == purpose,
            OTP.is_active.is_(True)
        )
        .with_for_update(skip_locked=True)
    )
    result = await session.execute(stmt)
    otp: OTP = result.scalar_one_or_none()

    if otp is None:
        return False
    
    if otp.expires_at <= now:
        otp.active = False
        await session.commit()
        return False
    
    if otp.attemps_left <= 0:
        otp.is_active = False
        await session.commit()
        return False

@authRouter.post(
    '/send-otp',
    response_model=None,
    status_code=status.HTTP_201_CREATED
)
async def send_otp(
    SendOtp: SendOtp,
    user: User = Depends(current_student_user),
    session: AsyncSession = Depends(get_async_session)
):
    pass



@authRouter.post(
    '/personal-data-update',
    response_model=None,
    status_code=status.HTTP_201_CREATED
)
async def profile_update(
    SendOtp: PersonalDataUpdate,
    user: User = Depends(current_student_user),
    session: AsyncSession = Depends(get_async_session)
):
    pass