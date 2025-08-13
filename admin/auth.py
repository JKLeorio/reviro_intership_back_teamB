from sqladmin import Admin
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from fastapi_users.exceptions import UserNotExists, InvalidPasswordException
from fastapi_users.authentication import JWTStrategy

from db.database import get_user_db_context, get_async_session_context
from api.auth import auth_backend, get_user_manager_context, SECRET

class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        email, password = form["username"], form["password"]
        auth_strategy: JWTStrategy = auth_backend.get_strategy()
        auth_strategy.lifetime_seconds = 3600

        async with get_async_session_context() as session:
            async with get_user_db_context(session) as user_db:
                async with get_user_manager_context(user_db) as user_manager:

                    try:
                        user = await user_manager.get_by_email(user_email=email)
                    except UserNotExists:
                        return False
                    
                    try:
                        user_manager.validate_password(
                            password=password, 
                            user=user
                            )
                        token = await auth_strategy.write_token(user=user)
                        request.session.update({"token": token})
                    except InvalidPasswordException:
                        return False
        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")
        auth_strategy: JWTStrategy = auth_backend.get_strategy()

        async with get_async_session_context() as session:
            async with get_user_db_context(session) as user_db:
                async with get_user_manager_context(user_db) as user_manager:
                    user = await auth_strategy.read_token(token, user_manager)
                    if user is None:
                        return False
                    return True
        return False
    
admin_authentication_backend = AdminAuth(secret_key=SECRET)