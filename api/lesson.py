import aiofiles
import os
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import Depends, APIRouter, HTTPException, status, Query, Form, UploadFile, File, Request
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.auth import current_student_user, current_teacher_user, current_admin_user
from db.types import Role

from models.group import Group
from models.lesson import Lesson, Classroom, Homework, HomeworkSubmission
from models.user import User

from schemas.lesson import (
    LessonRead, LessonCreate, LessonUpdate, LessonBase, ClassroomRead, ClassroomCreate, ClassroomUpdate, HomeworkRead,
    HomeworkCreate, HomeworkUpdate, HomeworkSubmissionRead, HomeworkSubmissionUpdate
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
    '''
    Returns a list of classrooms
    '''
    result = await db.execute(select(Classroom))
    return result.scalars().all()


@classroom_router.get('/{classroom_id}', response_model=ClassroomRead, status_code=status.HTTP_200_OK)
async def get_classroom(classroom_id: int, db: AsyncSession = Depends(get_async_session),
                        user: User = Depends(current_teacher_user)):
    '''
    Returns detailed classroom data by classroom id
    '''
    classroom = await get_classroom_or_404(classroom_id, db)
    return classroom


@classroom_router.post('/', response_model=ClassroomRead, status_code=status.HTTP_201_CREATED)
async def create_classroom(data: ClassroomCreate, db: AsyncSession = Depends(get_async_session),
                           user: User = Depends(current_admin_user)):
    '''
    Creates a classroom from the submitted data
    '''
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
    '''
    Updates a classroom by classroom id from the submitted data
    '''
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
    '''
    Delete classroom by classroom id
    '''
    classroom = await get_classroom_or_404(classroom_id, db)
    await db.delete(classroom)
    await db.commit()
    return {"detail": f"Classroom with id {classroom_id} has been deleted"}


# crud for lessons
async def get_group_or_404(group_id: int, db: AsyncSession):
    query = select(Group).where(Group.id == group_id).options(
        selectinload(Group.students),
        selectinload(Group.teacher)
    )
    result = await db.execute(query)
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group doesn't exist")
    return group


@lesson_router.get('/group/{group_id}/lessons', response_model=List[LessonRead], status_code=status.HTTP_200_OK)
async def get_lessons_by_groups(group_id: int,
                                limit: int = Query(10, ge=1, le=30, description="Limit number of lessons returned"),
                                offset: int = Query(0, ge=0, description="Offset for pagination"),
                                db: AsyncSession = Depends(get_async_session),
                                user: User = Depends(current_student_user)):
    '''
    Returns list of lessons by group id
    '''
    group = await get_group_or_404(group_id, db)
    students_ids = [student.id for student in group.students]
    if user.id != group.teacher_id and user.id not in students_ids and user.role != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not allowed")
    result = await db.execute(select(Lesson)
                              .where(Lesson.group_id == group_id)
                              .options(selectinload(Lesson.classroom),
                                       selectinload(Lesson.group),
                                       selectinload(Lesson.homework)).limit(limit).offset(offset))
    lessons = result.scalars().all()
    return lessons


@lesson_router.get('/lesson/{lesson_id}', response_model=LessonRead, status_code=status.HTTP_200_OK)

async def get_lesson_by_lesson_id(lesson_id: int, db: AsyncSession = Depends(get_async_session),

                              user: User = Depends(current_student_user)):
    '''
    Returns detailed classroom data by classroom id
    '''
    lesson = await db.get(Lesson, lesson_id, options=[selectinload(Lesson.classroom), selectinload(Lesson.group)
                                                      .selectinload(Group.students),
                                                      selectinload(Lesson.homework)])

    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson doesn't exist")

    students_ids = [student.id for student in lesson.group.students]

    if user.id != lesson.group.teacher_id and user.id not in students_ids and user.role != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not allowed")

    return lesson


@lesson_router.post('/group/{group_id}/new_lesson', response_model=LessonRead, status_code=status.HTTP_201_CREATED)
async def create_lesson(lesson_data: LessonCreate, group_id: int, db: AsyncSession = Depends(get_async_session),
                        user: User = Depends(current_teacher_user)):
    '''
    Creates a lesson from the submitted data
    '''
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
                                                         selectinload(Lesson.classroom),
                                                         selectinload(Lesson.homework))
                                  .where(Lesson.id == new_lesson.id))
    return new_lesson.scalar_one()


@lesson_router.patch('/lesson/{lesson_id}', response_model=LessonRead, status_code=status.HTTP_200_OK)
async def update_lesson(lesson_data: LessonUpdate, lesson_id: int,
                        db: AsyncSession = Depends(get_async_session), user: User = Depends(current_teacher_user)):
    '''
    Updates a lesson by lesson id from the submitted data
    '''
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
async def destroy_lesson(lesson_id: int, db: AsyncSession = Depends(get_async_session),
                         user: User = Depends(current_teacher_user)):
    '''
    Delete lesson by lesson id
    '''
    result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    lesson = result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson doesn't exist")
    if lesson.teacher_id != user.id and user.role != Role.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='You are not allowed')
    await db.delete(lesson)
    await db.commit()
    return {"detail": f"Lesson with id {lesson_id} has been deleted"}


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



# @homework_router.get("/my-homeworks", response_model=List[HomeworkRead], status_code=status.HTTP_200_OK)
# async def my_homeworks(db: AsyncSession = Depends(get_async_session),
#                                     user: User = Depends(current_student_user)):
#
#     homeworks = await get_homeworks_for_user(user.id, db)
#     return homeworks



@homework_router.get("/lesson/{lesson_id}/homework/{homework_id}", response_model=HomeworkRead,
                     status_code=status.HTTP_200_OK)
async def get_homework_by_id(lesson_id: int, homework_id: int, db: AsyncSession = Depends(get_async_session),
                             user: User = Depends(current_teacher_user)):

    result = await db.execute(select(Homework).where(Homework.id == homework_id, Homework.lesson_id == lesson_id))

    homework = result.scalar_one_or_none()
    if not homework:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Homework not found for this lesson"
        )
    return homework


@homework_router.post("/lesson/{lesson_id}/homework", response_model=HomeworkRead, status_code=status.HTTP_201_CREATED)
async def create_homework(lesson_id: int, data: HomeworkCreate,
                          db: AsyncSession = Depends(get_async_session),
                          user: User = Depends(current_teacher_user)):
    '''
    Creates a homework from the submitted data
    '''
    result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    lesson = result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson doesn't exist")
    if user.role not in (Role.TEACHER, Role.ADMIN):
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
    '''
    Updates a homework by homework id from the submitted data
    '''
    result = await db.execute(select(Homework).where(Homework.id == homework_id)
                              .options(selectinload(Homework.lesson)))
    homework = result.scalar_one_or_none()
    if not homework:
        raise HTTPException(status_code=404, detail="Homework not found")
    if user.role not in (Role.TEACHER, Role.ADMIN):
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
    '''
    Delete homework by homework id
    '''
    result = await db.execute(select(Homework).where(Homework.id == homework_id)
                              .options(selectinload(Homework.lesson)))
    homework = result.scalar_one_or_none()
    if not homework:
        raise HTTPException(status_code=404, detail="Homework not found")
    if user.id != homework.lesson.teacher_id and user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")

    await db.delete(homework)
    await db.commit()
    return {"detail": f"Homework with id {homework_id} has been deleted"}


@homework_submission_router.post('/{homework_id}', response_model=HomeworkSubmissionRead,
                                 status_code=status.HTTP_201_CREATED)
async def submit_homework(homework_id: int, content: Optional[str] = Form(None),
                          file: UploadFile | str = File(None),
                          db: AsyncSession = Depends(get_async_session), user: User = Depends(current_student_user)):
    if not file and not content:
        raise HTTPException(status_code=400, detail="Either file or content must be provided")

    file_path = None
    if file:
        os.makedirs(MEDIA_FOLDER, exist_ok=True)
        safe_datetime = datetime.now(timezone.utc).isoformat().replace(':', '_')
        filename = f"{user.id}_{safe_datetime}_{file.filename}"
        file_path = os.path.join(MEDIA_FOLDER, filename)
        with open(file_path, "wb") as f_out:
            f_out.write(await file.read())

    submission = HomeworkSubmission(
        homework_id=homework_id,
        student_id=user.id,
        file_path=file_path,
        content=content,
        submitted_at=datetime.now(timezone.utc).date()

    )

    db.add(submission)
    await db.commit()
    await db.refresh(submission)
    return submission


@homework_submission_router.get('/{homework_id}', response_model=List[HomeworkSubmissionRead],
                                status_code=status.HTTP_200_OK)
async def get_homework_submissions(homework_id: int, db: AsyncSession = Depends(get_async_session),
                           user: User = Depends(current_teacher_user)):
    result = await db.execute(select(Homework).where(Homework.id == homework_id))
    homework = result.scalar_one_or_none()
    if not homework:
        raise HTTPException(status_code=404, detail="Homework not found")
    if user.role not in (Role.TEACHER, Role.ADMIN):
        raise HTTPException(status_code=403, detail="You don't have enough permissions")

    submissions = await db.execute(select(HomeworkSubmission).where(HomeworkSubmission.homework_id == homework_id))
    return submissions.scalars().all()


async def get_homework_submission_or_none(homework_id, submission_id, db):
    result = await db.execute(select(HomeworkSubmission).where(HomeworkSubmission.homework_id == homework_id,
                                                               HomeworkSubmission.id == submission_id))
    return result.scalar_one_or_none()


@homework_submission_router.get("/{homework_id}/submission/{submission_id}/download",
                                name="download_submission")
async def download_submission(homework_id: int, submission_id: int, db: AsyncSession = Depends(get_async_session),
                              user: User = Depends(current_student_user)):
    submission = await get_homework_submission_or_none(homework_id, submission_id, db)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    if user.id != submission.student_id and user.role not in (Role.TEACHER, Role.ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='You are not allowed')

    if not submission.file_path:
        raise HTTPException(status_code=404, detail="No file attached")

    return FileResponse(submission.file_path, filename=os.path.basename(submission.file_path))


@homework_submission_router.get('/{homework_id}/submission/{submission_id}',
                                response_model=HomeworkSubmissionRead, status_code=status.HTTP_200_OK)
async def get_homework_submission(homework_id: int, submission_id: int, request: Request,
                                  db: AsyncSession = Depends(get_async_session),
                                  user: User = Depends(current_student_user)):
    submission = await get_homework_submission_or_none(homework_id, submission_id, db)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    if user.id != submission.student_id and user.role not in (Role.TEACHER, Role.ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='You are not allowed')
    download_url = None
    if submission.file_path:
        download_url = str(request.url_for("download_submission", homework_id=homework_id, submission_id=submission_id))
    return {
        "id": submission.id,
        "homework_id": submission.homework_id,
        "student_id": submission.student_id,
        "file_path": download_url,
        "content": submission.content,
        "submitted_at": submission.submitted_at,
    }


@homework_submission_router.patch('/{homework_id}/submission/{submission_id}', response_model=HomeworkSubmissionRead,
                                  status_code=status.HTTP_200_OK)
async def update_homework_submission(homework_id: int, submission_id: int, content: Optional[str] = None,
                                     file: UploadFile | str = File(None),
                                     db: AsyncSession = Depends(get_async_session),
                                     user: User = Depends(current_student_user)):
    submission = await get_homework_submission_or_none(homework_id, submission_id, db)

    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    if user.id != submission.student_id and user.role not in (Role.TEACHER, Role.ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='You are not allowed')

    if content:
        submission.content = content
    if file:
        os.makedirs(MEDIA_FOLDER, exist_ok=True)
        filename = f"{user.id}_{datetime.datetime.utcnow().isoformat()}_{file.filename}"
        file_path = os.path.join(MEDIA_FOLDER, filename)
        async with aiofiles.open(file_path, 'wb') as f_out:
            await f_out.write(await file.read())
        submission.file_path = file_path

    await db.commit()
    await db.refresh(submission)

    return submission


@homework_submission_router.delete('/{homework_id}/submission/{submission_id}', status_code=status.HTTP_200_OK)
async def destroy_homework_submission(homework_id: int, submission_id: int,
                                      db: AsyncSession = Depends(get_async_session),
                                      user: User = Depends(current_student_user)):

    submission = await get_homework_submission_or_none(homework_id, submission_id, db)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    if user.id != submission.student_id and user.role not in (Role.TEACHER, Role.ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='You are not allowed')

    await db.delete(submission)
    await db.commit()
    return {"detail": f"Submission with id {submission_id} has been deleted from homework with id {homework_id}"}
