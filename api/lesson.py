from typing import List
from fastapi import Depends, APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.auth import current_student_user

from models.group import Group
from models.lesson import Lesson, Classroom, Homework
from models.user import User

from schemas.lesson import (
    LessonRead
)

from db.database import get_async_session


lesson_router = APIRouter()


@lesson_router.get('/group/{group_id}/lessons', response_model=List[LessonRead], status_code=status.HTTP_200_OK)
async def get_lessons_by_groups(group_id: int, db: AsyncSession = Depends(get_async_session),
                                user: User = Depends(current_student_user)):

    group = await db.get(Group, group_id, options=[selectinload(Group.students), selectinload(Group.teacher)])

    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group doesn't exist")

    students_ids = [student.id for student in group.students]
    if user.id != group.teacher_id and user.id not in students_ids and user.role != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not allowed")
    result = await db.execute(select(Lesson)
                              .where(Lesson.group_id == group_id)
                              .options(selectinload(Lesson.classroom),
                                       selectinload(Lesson.group)
                                       )
                              )
    lessons = result.scalars().all()
    return lessons


@lesson_router.put('/')
