from typing import List

from fastapi import Depends, status, APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.auth import current_user

from db.database import get_async_session
from db.types import Role
from models.course import Course, Language, Level
from models.user import User

from schemas.course import LanguageRead, LanguageUpdate, LanguageBase, LevelRead, LevelBase, LevelUpdate
from schemas.course import CourseRead, CourseBase, CourseUpdate


course_router = APIRouter()
language_router = APIRouter()
level_router = APIRouter()


def get_superuser_or_admin(user: User = Depends(current_user)):
    if user.role == Role.ADMIN or user.is_superuser:
        return user
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have permission")


@language_router.get("/", response_model=List[LanguageRead], status_code=status.HTTP_200_OK)
async def languages_list(db: AsyncSession = Depends(get_async_session)):
    languages = await db.execute(select(Language))
    return languages.scalars().all()


@language_router.get('/{id}', response_model=LanguageRead, status_code=status.HTTP_200_OK)
async def get_language(id: int, db: AsyncSession = Depends(get_async_session)):
    result = await db.execute(select(Language).where(Language.id == id))
    language = result.scalar_one_or_none()

    if language is None:
        raise HTTPException(status_code=404, detail="Language not found")

    return language


@language_router.post("/", response_model=LanguageRead, status_code=status.HTTP_201_CREATED)
async def create_language(language_data: LanguageBase, db: AsyncSession = Depends(get_async_session),
                          user: User = Depends(get_superuser_or_admin)):
    new_language = Language(**language_data.model_dump())
    db.add(new_language)
    await db.commit()
    await db.refresh(new_language)
    return new_language


@language_router.patch("/{id}", response_model=LanguageRead, status_code=status.HTTP_200_OK)
async def update_language(id: int, language_data: LanguageUpdate, db: AsyncSession = Depends(get_async_session),
                          user: User = Depends(get_superuser_or_admin)):
    result = await db.execute(select(Language).where(Language.id == id))
    language = result.scalar_one_or_none()
    if language is None:
        raise HTTPException(status_code=404, detail="Language not found")
    update_data = language_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(language, key, value)
    await db.commit()
    await db.refresh(language)
    return language


@language_router.delete("/{id}", status_code=status.HTTP_200_OK)
async def destroy_language(id: int, db: AsyncSession = Depends(get_async_session),
                           user: User = Depends(get_superuser_or_admin)):
    result = await db.execute(select(Language).where(Language.id == id))
    language = result.scalar_one_or_none()

    if language is None:
        raise HTTPException(status_code=404, detail="Language not found")

    await db.delete(language)
    await db.commit()
    return {"detail": f"Language with id {id} has been deleted"}


@level_router.get("/", response_model=List[LevelRead], status_code=status.HTTP_200_OK)
async def levels_list(db: AsyncSession = Depends(get_async_session)):
    levels = await db.execute(select(Level))
    return levels.scalars().all()


@level_router.get("/{id}", response_model=LevelRead, status_code=status.HTTP_200_OK)
async def get_level(id: int, db: AsyncSession = Depends(get_async_session)):
    result = await db.execute(select(Level).where(Level.id == id))
    level = result.scalar_one_or_none()
    if level is None:
        raise HTTPException(status_code=404, detail="Level not found")
    return level


@level_router.post("/", response_model=LevelRead, status_code=status.HTTP_201_CREATED)
async def create_level(level_data: LevelBase, db: AsyncSession = Depends(get_async_session),
                       user: User = Depends(get_superuser_or_admin)):
    new_level = Level(**level_data.model_dump())
    db.add(new_level)
    await db.commit()
    await db.refresh(new_level)
    return new_level


@level_router.patch("/{id}", response_model=LevelRead, status_code=status.HTTP_200_OK)
async def update_level(id: int, level_data: LevelUpdate, db: AsyncSession = Depends(get_async_session),
                       user: User = Depends(get_superuser_or_admin)):
    result = await db.execute(select(Level).where(Level.id == id))
    level = result.scalar_one_or_none()
    if level is None:
        raise HTTPException(status_code=404, detail="Level not found")

    update_data = level_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(level, key, value)
    await db.commit()
    await db.refresh(level)
    return level


@level_router.delete("/{id}", status_code=status.HTTP_200_OK)
async def destroy_level(id: int, db: AsyncSession = Depends(get_async_session),
                        user: User = Depends(get_superuser_or_admin)):
    result = await db.execute(select(Level).where(Level.id == id))
    level = result.scalar_one_or_none()
    if level is None:
        raise HTTPException(status_code=404, detail="Level not found")
    await db.delete(level)
    await db.commit()
    return {"detail": f"Level with id {id} has been deleted"}


@course_router.get("/", response_model=List[CourseRead], status_code=status.HTTP_200_OK)
async def courses_list(db: AsyncSession = Depends(get_async_session)):
    result = await db.execute(
        select(Course).options(
            selectinload(Course.language),
            selectinload(Course.level)
        )
    )
    return result.scalars().all()


@course_router.get("/{id}", response_model=CourseRead, status_code=status.HTTP_200_OK)
async def get_course(id: int, db: AsyncSession = Depends(get_async_session)):
    result = await db.execute(select(Course).where(Course.id == id)
                              .options(selectinload(Course.language))
                              .options(selectinload(Course.level)))
    course = result.scalar_one_or_none()
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@course_router.post("/", response_model=CourseRead, status_code=status.HTTP_201_CREATED)
async def create_course(course_data: CourseBase, db: AsyncSession = Depends(get_async_session),
                        user: User = Depends(get_superuser_or_admin)):
    language_res = await db.execute(select(Language).where(Language.name == course_data.language_name))
    language_obj = language_res.scalar_one_or_none()
    if not language_obj:
        raise HTTPException(status_code=404, detail="Language not found")

    level_res = await db.execute(select(Level).where(Level.code == course_data.level_code))
    level_obj = level_res.scalar_one_or_none()
    if not level_obj:
        raise HTTPException(status_code=404, detail="Level not found")

    new_course = Course(
        name=course_data.name,
        price=course_data.price,
        description=course_data.description,
        language_id=language_obj.id,
        level_id=level_obj.id
    )
    db.add(new_course)
    await db.commit()
    await db.refresh(new_course)
    result = await db.execute(
        select(Course)
        .where(Course.id == new_course.id)
        .options(
            selectinload(Course.language),
            selectinload(Course.level)
        )
    )
    return result.scalar_one()


@course_router.patch("/{id}", response_model=CourseRead, status_code=status.HTTP_200_OK)
async def update_course(id: int, course_data: CourseUpdate, db: AsyncSession = Depends(get_async_session),
                        user: User = Depends(get_superuser_or_admin)):
    result = await db.execute(select(Course).where(Course.id == id))
    course = result.scalar_one_or_none()
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")

    update_data = course_data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(course, key, value)

    await db.commit()
    await db.refresh(course)
    result = await db.execute(
        select(Course)
        .where(Course.id == course.id)
        .options(
            selectinload(Course.language),
            selectinload(Course.level)
        )
    )
    return result.scalar_one()


@course_router.delete("/{id}", status_code=status.HTTP_200_OK)
async def destroy_course(id: int, db: AsyncSession = Depends(get_async_session),
                         user: User = Depends(get_superuser_or_admin)):
    result = await db.execute(select(Course).where(Course.id == id))
    course = result.scalar_one_or_none()
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    await db.delete(course)
    await db.commit()
    return {"detail": f"Course with id {id} has been deleted"}
