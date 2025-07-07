import os
import datetime
from typing import List
from fastapi import Depends, APIRouter, HTTPException, status, Query, Form, UploadFile, File
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.auth import current_student_user, current_teacher_user, current_admin_user
from api.group import group_router

from models.group import Group
from models.lesson import Lesson, Classroom, Homework, HomeworkSubmission
from models.user import User

from schemas.lesson import (
    LessonRead, LessonCreate, LessonUpdate, ClassroomRead, ClassroomCreate, ClassroomUpdate, HomeworkRead,
    HomeworkCreate, HomeworkUpdate, HomeworkSubmissionCreate, HomeworkSubmissionRead
)

from db.database import get_async_session

lesson_router = APIRouter()
classroom_router = APIRouter()
homework_router = APIRouter()
homework_submission_router = APIRouter()


MEDIA_FOLDER = "media/homework_submissions"
os.makedirs(MEDIA_FOLDER, exist_ok=True)


# crud for classroom

async def get_classroom_or_404(classroom_id: int, db: AsyncSession):
    result = await db.execute(select(Classroom).where(Classroom.id == classroom_id))
    classroom = result.scalar_one_or_none()
    if not classroom:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom doesn't exist")
    return classroom


def get_group_students(group):
    students_ids = [student.id for student in group.students]


@classroom_router.get('/', response_model=List[ClassroomRead], status_code=status.HTTP_200_OK)
async def get_all_classrooms(db: AsyncSession = Depends(get_async_session), user: User = Depends(current_teacher_user)):
    result = await db.execute(select(Classroom))
    return result.scalars().all()


@classroom_router.get('/{classroom_id}', response_model=ClassroomRead, status_code=status.HTTP_200_OK)
async def get_classroom(classroom_id: int, db: AsyncSession = Depends(get_async_session),
                        user: User = Depends(current_teacher_user)):
    classroom = await get_classroom_or_404(classroom_id, db)
    return classroom


@classroom_router.post('/', response_model=ClassroomRead, status_code=status.HTTP_201_CREATED)
async def create_classroom(data: ClassroomCreate, db: AsyncSession = Depends(get_async_session),
                           user: User = Depends(current_admin_user)):
    data = data.model_dump()
    new_classroom = Classroom(**data)
    db.add(new_classroom)
    await db.commit()
    await db.refresh(new_classroom)
    return new_classroom


@classroom_router.patch('/{classroom_id}', response_model=ClassroomRead, status_code=status.HTTP_200_OK)
async def update_classroom(classroom_id: int, data: ClassroomUpdate,
                           db: AsyncSession = Depends(get_async_session),
                           user: User = Depends(current_admin_user)):
    classroom = await get_classroom_or_404(classroom_id, db)
    data = data.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(classroom, key, value)

    await db.commit()
    await db.refresh(classroom)
    return classroom


@classroom_router.delete('/{classroom_id}', status_code=status.HTTP_200_OK)
async def destroy_classroom(classroom_id: int, db: AsyncSession = Depends(get_async_session),
                            user: User = Depends(current_admin_user)):
    classroom = await get_classroom_or_404(classroom_id, db)
    await db.delete(classroom)
    await db.commit()
    return {"detail": f"Classroom with id {classroom_id} has been deleted"}


# crud for lessons
async def get_group_or_404(group_id: int,  db: AsyncSession):
    group = await db.get(Group, group_id, options=[selectinload(Group.students), selectinload(Group.teacher)])
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group doesn't exist")
    return group


@lesson_router.get('/group/{group_id}/lessons', response_model=List[LessonRead], status_code=status.HTTP_200_OK)
async def get_lessons_by_groups(group_id: int,
                                limit: int = Query(10, ge=1, le=30, description="Limit number of lessons returned"),
                                offset: int = Query(0, ge=0, description="Offset for pagination"),
                                db: AsyncSession = Depends(get_async_session),
                                user: User = Depends(current_student_user)):

    group = await get_group_or_404(group_id, db)
    students_ids = [student.id for student in group.students]
    if user.id != group.teacher_id and user.id not in students_ids and user.role != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not allowed")
    result = await db.execute(select(Lesson)
                              .where(Lesson.group_id == group_id)
                              .options(selectinload(Lesson.classroom),
                                       selectinload(Lesson.group)).limit(limit).offset(offset))
    lessons = result.scalars().all()
    return lessons


@lesson_router.get('/lesson/{lesson_id}', response_model=LessonRead, status_code=status.HTTP_200_OK)
async def get_lesson_by_group(lesson_id: int, db: AsyncSession = Depends(get_async_session),
                              user: User = Depends(current_student_user)):

    lesson = await db.get(Lesson, lesson_id, options=[selectinload(Lesson.classroom), selectinload(Lesson.group)
                                                      .selectinload(Group.students)])

    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson doesn't exist")

    students_ids = [student.id for student in lesson.group.students]

    if user.id != lesson.group.teacher_id and user.id not in students_ids and user.role != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not allowed")

    return lesson


@lesson_router.post('/group/{group_id}/new_lesson', response_model=LessonRead, status_code=status.HTTP_201_CREATED)
async def create_lesson(lesson_data: LessonCreate, group_id: int, db: AsyncSession = Depends(get_async_session),
                        user: User = Depends(current_teacher_user)):

    group = await get_group_or_404(group_id, db)

    # if group.teacher_id != user.id:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not allowed")

    new_lesson_data = lesson_data.model_dump()
    new_lesson_data['group_id'] = group_id
    # new_lesson_data['teacher_id'] = user.id
    new_lesson = Lesson(**new_lesson_data)
    db.add(new_lesson)
    await db.commit()
    await db.refresh(new_lesson)
    new_lesson = await db.execute(select(Lesson).options(selectinload(Lesson.group),
                                                         selectinload(Lesson.classroom))
                                  .where(Lesson.id == new_lesson.id))
    return new_lesson.scalar_one()


@lesson_router.patch('/lesson/{lesson_id}', response_model=LessonRead, status_code=status.HTTP_200_OK)
async def update_lesson(lesson_data: LessonUpdate, lesson_id: int,
                        db: AsyncSession = Depends(get_async_session), user: User = Depends(current_teacher_user)):

    lesson = await db.get(Lesson, lesson_id, options=[selectinload(Lesson.classroom)])
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson doesn't exist")

    if lesson.teacher_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not allowed")

    new_data = lesson_data.model_dump(exclude_unset=True)
    for key, value in new_data.items():
        setattr(lesson, key, value)

    await db.commit()
    await db.refresh(lesson)
    lesson = await db.execute(select(Lesson).where(Lesson.id == lesson_id).
                              options(selectinload(Lesson.group),
                                      selectinload(Lesson.classroom)))
    return lesson.scalar_one()


@lesson_router.delete('/lesson/{lesson_id}', status_code=status.HTTP_200_OK)
async def destroy_lesson(group_id: int, lesson_id: int, db: AsyncSession = Depends(get_async_session),
                         user: User = Depends(current_teacher_user)):
    result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    lesson = result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson doesn't exist")
    await db.delete(lesson)
    await db.commit()
    return {"detail": f"Lesson with id {lesson_id} has been deleted from group with id {group_id}"}


async def get_homeworks_for_user(user_id, db: AsyncSession):
    result = await db.execute(select(User).where(User.id == user_id).
                              options(selectinload(User.groups_joined)
                                      .selectinload(Group.lessons)
                                      .selectinload(Lesson.homeworks)
                                      )
                              )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    homeworks = []
    for group in user.groups_joined:
        for lesson in group.lessons:
            homeworks.extend(lesson.homeworks)
    return homeworks


@homework_router.get("/my-homeworks", response_model=List[HomeworkRead], status_code=status.HTTP_200_OK)
async def my_homeworks(db: AsyncSession = Depends(get_async_session),
                                    user: User = Depends(current_student_user)):

    homeworks = await get_homeworks_for_user(user.id, db)
    return homeworks


@homework_router.get("/{homework_id}", response_model=HomeworkRead, status_code=status.HTTP_200_OK)
async def get_homework_by_id(homework_id: int, db: AsyncSession = Depends(get_async_session),
                             user: User = Depends(current_teacher_user)):
    result = await db.execute(select(Homework).where(Homework.id == homework_id))
    homework = result.scalar_one_or_none()
    if not homework:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Homework not found")
    return homework


@homework_router.post("/lesson/{lesson_id}/homework", response_model=HomeworkRead, status_code=status.HTTP_201_CREATED)
async def create_homework(lesson_id: int, data: HomeworkCreate,
                          db: AsyncSession = Depends(get_async_session),
                          user: User = Depends(current_teacher_user)):
    result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    lesson = result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson doesn't exist")
    if user.id != lesson.teacher_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='You are not allowed')
    new_homework_data = data.model_dump()
    new_homework_data['lesson_id'] = lesson_id

    new_homework = Homework(**new_homework_data)
    db.add(new_homework)
    await db.commit()
    await db.refresh(new_homework)
    return new_homework


@homework_router.patch("/{homework_id}", response_model=HomeworkRead, status_code=status.HTTP_200_OK)
async def update_homework(homework_id: int, data: HomeworkUpdate, db: AsyncSession = Depends(get_async_session),
                          user: User = Depends(current_teacher_user)):
    result = await db.execute(select(Homework).where(Homework.id == homework_id)
                              .options(selectinload(Homework.lesson)))
    homework = result.scalar_one_or_none()
    if not homework:
        raise HTTPException(status_code=404, detail="Homework not found")
    if user.id != homework.lesson.teacher_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    new_data = data.model_dump(exclude_unset=True)
    for key, value in new_data.items():
        setattr(homework, key, value)

    await db.commit()
    await db.refresh(homework)

    return homework


@homework_router.delete("/{homework_id}", status_code=status.HTTP_200_OK)
async def destroy_homework(homework_id: int, db: AsyncSession = Depends(get_async_session),
                           user: User = Depends(current_teacher_user)):
    result = await db.execute(select(Homework).where(Homework.id == homework_id)
                              .options(selectinload(Homework.lesson)))
    homework = result.scalar_one_or_none()
    if not homework:
        raise HTTPException(status_code=404, detail="Homework not found")
    if user.id != homework.lesson.teacher_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    await db.delete(homework)
    await db.commit()
    return {"detail": f"Homework with id {homework_id} has been deleted"}


# @homework_submission_router.post('/', response_model=HomeworkSubmissionRead,
#                                  status_code=status.HTTP_201_CREATED)
# async def submit_homework(homework_id: int = Form(...), content: str = Form(None), file: UploadFile = File(None),
#                           db: AsyncSession = Depends(get_async_session), user: User = Depends(current_student_user)):
#     if not file and not content:
#         raise HTTPException(status_code=400, detail="Either file or contend must be provided")
#
#     file_path = None
#     if file:
#         filename = f"{user.id}_{datetime.utcnow().isoformat()}_{file.filename}"
#         file_path = os.path.join(MEDIA_FOLDER, filename)
#         with open(file_path, "wb") as f_out:
#             f_out.write(await file.read())
#
#     submission = HomeworkSubmission(
#         homework_id=homework_id,
#         student_id = user.id,
#         file_path=file_path,
#         content=content,
#         submitted_at=datetime.utcnow().date
#     )
#
#     db.add(submission)
#     await db.commit()
#     await db.refresh(submission)
#     return submission
