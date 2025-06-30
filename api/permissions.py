from typing import Optional
from fastapi import Depends, HTTPException, status

from sqlalchemy import Select, select
from sqlalchemy.orm import class_mapper, selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession


from db.dbbase import Base
from db.database import get_async_session
from models.group import Group
from models.user import User

from functools import reduce

def require_roles(*roles : str):
    """
    Dependenci for checking user permissions by roles
    """
    from .auth import current_user
    
    async def check_roles(user : User = Depends(current_user)):
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"detail" : "you don't have enough permissions"})
        return user
    return check_roles



# def find_user_field(model: Base) -> str | None:
#     '''
#     find table field related with users
#     '''
#     mapper = class_mapper(model)
#     for rel in mapper.relationships:
#         if rel.mapper.class_ is User:
#             return rel.key
        
#     for column in model.__table__.columns:
#         for fk in column.foreign_keys:
#             if fk.column.table.name == 'users' and fk.column.name == 'id':
#                 return column.key
            
#     return None


# async def has_object_permission(
#         ojb_id: int,
#         model: Base,
#         allowed_roles: list[str],
#         user: User,
#         session: AsyncSession,
# ):
#     '''
#     Checks if the user has rights such as owner
#     '''
#     obj = await session.get(model, ojb_id)
#     if not obj:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
#     if user.role in allowed_roles:
#         return obj
    
#     field = find_user_field(model=model)

#     if not field:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN, 
#             detail={"detail":"no user-related field found"}
#             )
    
#     related_user = getattr(obj, field)
#     if isinstance(related_user, User):
#         if related_user.id != user.id:
#             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
#     else:
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
#     return obj



# def resolve_path(obj, attr_path: str) -> Base:
#     try:
#         return reduce(getattr, attr_path.split('.'), obj)
#     except AttributeError:
#         return None


# async def check_group_permission(
#         query: Select,
#         model: Base,
#         group_path: str,
#         allowed_roles: str,
#         session: AsyncSession,
#         user: User,
# ):
#     '''
#     checks if the user has group-based viewing permissions
#     '''
#     path_parts = group_path.split(".")
#     load_option = reduce(lambda acc, attr: joinedload(attr) if acc is None else acc.joinedload(attr), path_parts, None)

#     result = await session.execute(query.options(load_option))
#     obj = result.scalar_one_or_none()

#     if user.role in allowed_roles:
#         return result

#     if not obj:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
#     group: Group = resolve_path(obj=obj, group_path=group_path)

#     if not isinstance(group, Group):
#         raise HTTPException(403, detail="Group not found")
    
#     if user not in await group.awaitable_attrs.students:
#         raise HTTPException(403, detail="Access denied")
    
#     return result