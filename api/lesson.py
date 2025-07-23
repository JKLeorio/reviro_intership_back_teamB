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
from db.types import AttendanceStatus, Role

from models.group import Group
from models.lesson import Attendance, Lesson, Classroom, Homework, HomeworkSubmission, HomeworkReview
from models.user import User

from schemas.lesson import (
    LessonRead, LessonCreate, LessonUpdate, LessonBase, ClassroomRead, ClassroomCreate, ClassroomUpdate, HomeworkRead,
    HomeworkSubmissionRead, HomeworkReviewCreate, HomeworkReviewRead, HomeworkReviewBase,

    HomeworkReviewUpdate, HomeworkSubmissionShort
)

from db.database import get_async_session

lesson_router = APIRouter()
classroom_router = APIRouter()
homework_router = APIRouter()
homework_submission_router = APIRouter()
homework_review_router = APIRouter()


MEDIA_FOLDER = "media/homework_submissions"
HOMEWORK_FOLDER = "media/homeworks"
os.makedirs(HOMEWORK_FOLDER, exist_ok=True)
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
    return students_ids


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


@lesson_router.get('/{lesson_id}', response_model=LessonRead, status_code=status.HTTP_200_OK)
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


@lesson_router.post('/group/{group_id}/new_lesson', response_model=LessonBase, status_code=status.HTTP_201_CREATED)
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
    await db.flush()
    await db.refresh(
        new_lesson
        )
    
    students = await new_lesson.group.awaitable_attrs.students
    for student in students:
        db.add(Attendance(
                status=AttendanceStatus.ABSENT,
                student_id=student.id,
                lesson_id=new_lesson.id
                )
            )
    await db.commit()
    # new_lesson = await db.execute(select(Lesson).options(selectinload(Lesson.group),
    #                                                      selectinload(Lesson.classroom),
    #                                                      selectinload(Lesson.homework))
    #                               .where(Lesson.id == new_lesson.id))
    # return new_lesson.scalar_one()
    await db.refresh(
        new_lesson,
        attribute_names=[
            'group',
            'classroom',
            'homework'
        ]
    )
    return new_lesson


@lesson_router.patch('/{lesson_id}', response_model=LessonBase, status_code=status.HTTP_200_OK)
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


@lesson_router.delete('/{lesson_id}', status_code=status.HTTP_200_OK)
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


@homework_router.get("/{homework_id}", response_model=HomeworkRead, status_code=status.HTTP_200_OK)
async def get_homework_by_id(homework_id: int, db: AsyncSession = Depends(get_async_session),
                             user: User = Depends(current_teacher_user)):
    if user.role not in (Role.TEACHER, Role.ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='You are not allowed')

    result = await db.execute(select(Homework).where(Homework.id == homework_id)
                              .options(selectinload(Homework.submissions)))

    homework = result.scalar_one_or_none()
    if not homework:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Homework not found"
        )
    return homework


@homework_router.post("/lesson/{lesson_id}", response_model=HomeworkRead, status_code=status.HTTP_201_CREATED)
async def create_homework(lesson_id: int, deadline: datetime = Form(),
                          description: Optional[str] = Form(None), file: UploadFile | str = File(None),
                          db: AsyncSession = Depends(get_async_session),
                          user: User = Depends(current_teacher_user)):
    '''
    Creates a homework from the submitted data
    '''
    if not file and not description:
        raise HTTPException(status_code=400, detail="Either file or content must be provided")
    lesson = await db.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson doesn't exist")
    if lesson.teacher_id != user.id and user.role != Role.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='You are not allowed')
    file_path = None
    if file:
        os.makedirs(HOMEWORK_FOLDER, exist_ok=True)
        filename = f"{lesson.name}_{file.filename}"
        file_path = os.path.join(HOMEWORK_FOLDER, filename)
        async with aiofiles.open(file_path, 'wb') as f_out:
            await f_out.write(await file.read())

    new_homework = Homework(
        lesson_id=lesson_id,
        created_at=datetime.now(timezone.utc),
        file_path=file_path,
        description=description,
        deadline=deadline
    )
    db.add(new_homework)
    await db.commit()
    await db.refresh(new_homework)
    return new_homework


async def get_homework_or_none(homework_id, db, user):
    result = await db.execute(select(Homework).where(Homework.id == homework_id).options(selectinload(Homework.lesson)
                                                                                         .selectinload(Lesson.group)
                                                                                         .selectinload(Group.students)
                                                                                         ))
    homework = result.scalar_one_or_none()
    return homework


@homework_router.get("/{homework_id}/download", name="download_homework")
async def download_submission(homework_id: int, db: AsyncSession = Depends(get_async_session),
                              user: User = Depends(current_student_user)):
    homework = await get_homework_or_none(homework_id, db, user)
    if user.role not in (Role.ADMIN, Role.TEACHER) and user.id not in get_group_students(homework.lesson.group):
        raise HTTPException(status_code=403, detail="You are not allowed")
    if not homework:
        raise HTTPException(status_code=404, detail="Submission not found")
    if user.id not in get_group_students(homework.lesson.group):
        raise HTTPException(status_code=403, detail="You are not allowed")
    if not homework.file_path:
        raise HTTPException(status_code=404, detail="No file attached")

    return FileResponse(homework.file_path, filename=os.path.basename(homework.file_path))


@homework_router.patch("/{homework_id}", response_model=HomeworkRead, status_code=status.HTTP_200_OK)
async def update_homework(homework_id: int, deadline: datetime = Form(),
                          description: Optional[str] = Form(None), file: UploadFile | str = File(None),
                          db: AsyncSession = Depends(get_async_session),
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

    if deadline:
        homework.deadline = deadline
    if description:
        homework.description = description
    if file:
        if homework.file_path and os.path.exists(homework.file_path):
            os.remove(homework.file_path)
        os.makedirs(HOMEWORK_FOLDER, exist_ok=True)
        filename = f"{homework_id}_{file.filename}"
        file_path = os.path.join(HOMEWORK_FOLDER, filename)
        async with aiofiles.open(file_path, 'wb') as f_out:
            await f_out.write(await file.read())
        homework.file_path = file_path

    await db.commit()
    await db.refresh(homework)

    return homework


@homework_router.patch('/{homework_id}/remove-file', status_code=status.HTTP_200_OK)
async def remove_file_from_homework(homework_id: int, db: AsyncSession = Depends(get_async_session),
                              user: User = Depends(current_teacher_user)):
    result = await db.execute(select(Homework).where(Homework.id == homework_id)
                              .options(selectinload(Homework.lesson)))
    homework = result.scalar_one_or_none()
    if not homework:
        raise HTTPException(status_code=404, detail="Homework not found")
    if user.id != homework.lesson.teacher_id and user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")
    if homework.file_path and os.path.exists(homework.file_path):
        try:
            os.remove(homework.file_path)
        except:
            pass
    homework.file_path = None

    await db.commit()
    await db.refresh(homework)
    return {"detail": f"File removed from homework with id {homework_id}"}



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


@homework_submission_router.post('/homework/{homework_id}', response_model=HomeworkSubmissionShort,
                                 status_code=status.HTTP_201_CREATED)
async def submit_homework(homework_id: int, content: Optional[str] = Form(None),
                          file: UploadFile | str = File(None),
                          db: AsyncSession = Depends(get_async_session), user: User = Depends(current_student_user)):
    homework = await get_homework_or_none(homework_id, db, user)
    if not homework:
        raise HTTPException(status_code=404, detail=f'Homework with id {homework_id} not found')

    if not homework:
        raise HTTPException(status_code=404, detail=f'Homework with id {homework_id} not found')

    students_ids = get_group_students(homework.lesson.group)
    if user.role != Role.ADMIN and user.role != Role.TEACHER and user.id not in students_ids:
        raise HTTPException(status_code=403, detail="You are not allowed")

    if not file and not content:
        raise HTTPException(status_code=400, detail="Either file or content must be provided")

    existing_submission_result = await db.execute(select(HomeworkSubmission).where(
        (HomeworkSubmission.homework_id == homework_id) & (HomeworkSubmission.student_id == user.id)))
    existing_submission = existing_submission_result.scalar_one_or_none()
    if existing_submission:
        raise HTTPException(status_code=400, detail="You have already submitted this homework")

    file_path = None
    if file:

        os.makedirs(MEDIA_FOLDER, exist_ok=True)
        filename = f"{user.first_name}-{user.last_name}_{file.filename}"
        file_path = os.path.join(MEDIA_FOLDER, filename)
        async with aiofiles.open(file_path, "wb") as f_out:
            await f_out.write(await file.read())

    submission = HomeworkSubmission(
        homework_id=homework_id,
        student_id=user.id,
        file_path=file_path,
        content=content,
        submitted_at=datetime.now(timezone.utc)

    )

    db.add(submission)
    await db.commit()
    await db.refresh(submission)
    return submission


@homework_submission_router.get('/homework/{homework_id}', response_model=List[HomeworkSubmissionRead],
                                status_code=status.HTTP_200_OK)
async def get_homework_submissions(homework_id: int, db: AsyncSession = Depends(get_async_session),
                           user: User = Depends(current_teacher_user)):
    result = await db.execute(select(Homework).where(Homework.id == homework_id))
    homework = result.scalar_one_or_none()
    if not homework:
        raise HTTPException(status_code=404, detail="Homework not found")
    if user.role not in (Role.TEACHER, Role.ADMIN):
        raise HTTPException(status_code=403, detail="You don't have enough permissions")

    submissions = await db.execute(select(HomeworkSubmission).where(HomeworkSubmission.homework_id == homework_id)
                                   .options(selectinload(HomeworkSubmission.review)))
    return submissions.scalars().all()


@homework_submission_router.get('/homework/{homework_id}/my_submission', response_model=HomeworkSubmissionRead,
                                status_code=status.HTTP_200_OK)
async def get_my_homework_submission(homework_id: int, db: AsyncSession = Depends(get_async_session),
                                     user: User = Depends(current_student_user)):
    homework = await get_homework_or_none(homework_id, db, user)
    if not homework:
        raise HTTPException(status_code=404, detail="Submission not found")
    if user.id not in get_group_students(homework.lesson.group):
        raise HTTPException(status_code=403, detail="You are not allowed")
    result = await db.execute(
        select(HomeworkSubmission)
        .where(
            HomeworkSubmission.homework_id == homework_id,
            HomeworkSubmission.student_id == user.id
        )
        .options(selectinload(HomeworkSubmission.review))
    )
    submission = result.scalar_one_or_none()
    return submission


async def get_homework_submission_or_none(submission_id, db):
    result = await db.execute(select(HomeworkSubmission).where(HomeworkSubmission.id == submission_id)
                              .options(selectinload(HomeworkSubmission.review)))
    return result.scalar_one_or_none()


@homework_submission_router.get("/{submission_id}/download",
                                name="download_submission")
async def download_submission(submission_id: int, db: AsyncSession = Depends(get_async_session),
                              user: User = Depends(current_student_user)):
    submission = await get_homework_submission_or_none(submission_id, db)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    if user.id != submission.student_id and user.role not in (Role.TEACHER, Role.ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='You are not allowed')

    if not submission.file_path:
        raise HTTPException(status_code=404, detail="No file attached")

    return FileResponse(submission.file_path, filename=os.path.basename(submission.file_path))


@homework_submission_router.get('/{submission_id}',
                                response_model=HomeworkSubmissionRead, status_code=status.HTTP_200_OK)
async def get_homework_submission(submission_id: int, request: Request,
                                  db: AsyncSession = Depends(get_async_session),
                                  user: User = Depends(current_student_user)):
    submission = await get_homework_submission_or_none(submission_id, db)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    if user.id != submission.student_id and user.role not in (Role.TEACHER, Role.ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='You are not allowed')
    return submission


@homework_submission_router.patch('/{submission_id}', response_model=HomeworkSubmissionShort,
                                  status_code=status.HTTP_200_OK)
async def update_homework_submission(submission_id: int, content: Optional[str] = None,
                                     file: UploadFile | str | None = File(None),
                                     db: AsyncSession = Depends(get_async_session),
                                     user: User = Depends(current_student_user)):
    submission = await get_homework_submission_or_none(submission_id, db)

    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    if user.id != submission.student_id and user.role not in (Role.TEACHER, Role.ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='You are not allowed')

    if content:
        submission.content = content
    if file:
        if submission.file_path and os.path.exists(submission.file_path):
            os.remove(submission.file_path)
        os.makedirs(MEDIA_FOLDER, exist_ok=True)
        filename = f"{user.id}_{file.filename}"
        file_path = os.path.join(MEDIA_FOLDER, filename)
        async with aiofiles.open(file_path, 'wb') as f_out:
            await f_out.write(await file.read())
        submission.file_path = file_path

    await db.commit()
    await db.refresh(submission)

    return submission


@homework_submission_router.patch('/{submission_id}/remove-file', status_code=status.HTTP_200_OK)
async def remove_file_from_submission(submission_id: int, db: AsyncSession = Depends(get_async_session),
                                      user: User = Depends(current_student_user)):
    result = await db.execute(select(HomeworkSubmission).where(HomeworkSubmission.id == submission_id))
    submission = result.scalar_one_or_none()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    if user.role != Role.ADMIN and user.id != submission.student_id:
        raise HTTPException(status_code=403, detail="You don't have enough permissions")
    if submission.file_path and os.path.exists(submission.file_path):
        try:
            os.remove(submission.file_path)
        except:
            pass
    submission.file_path = None
    await db.commit()
    await db.refresh(submission)
    return {"detail": f"File removed from submission with id {submission_id}"}


@homework_submission_router.delete('/{submission_id}', status_code=status.HTTP_200_OK)
async def destroy_homework_submission(submission_id: int,
                                      db: AsyncSession = Depends(get_async_session),
                                      user: User = Depends(current_student_user)):

    submission = await get_homework_submission_or_none(submission_id=submission_id, db=db)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    if user.id != submission.student_id and user.role not in (Role.TEACHER, Role.ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='You are not allowed')

    await db.delete(submission)
    await db.commit()
    return {"detail": f"Submission with id {submission_id} has been deleted"}


@homework_review_router.post('/submission/{submission_id}', response_model=HomeworkReviewRead,
                             status_code=status.HTTP_201_CREATED)
async def create_homework_review(submission_id: int, data: HomeworkReviewCreate,
                                 db: AsyncSession = Depends(get_async_session),
                                 user: User = Depends(current_teacher_user)):
    result = await db.execute(select(HomeworkSubmission).where(HomeworkSubmission.id == submission_id)
                              .options(selectinload(HomeworkSubmission.homework)
                                       .selectinload(Homework.lesson)))
    submission = result.scalar_one_or_none()
    if submission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
    if user.role == Role.TEACHER and user.id != submission.homework.lesson.teacher_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='You are not allowed')
    existing_review = (await db.execute(select(HomeworkReview)
                                       .where((HomeworkReview.submission_id == submission_id) &
                                              (HomeworkReview.teacher_id == user.id)))).scalar_one_or_none()
    if existing_review:
        raise HTTPException(status_code=400, detail='You have already review this submission')
    new_data = data.model_dump(exclude_unset=True)
    new_data['teacher_id'] = user.id
    new_data['submission_id'] = submission_id
    review = HomeworkReview(**new_data)
    db.add(review)
    await db.commit()
    await db.refresh(review)
    return review


@homework_review_router.get('/{review_id}', response_model=HomeworkReviewBase, status_code=status.HTTP_200_OK)
async def get_homework_review_by_id(review_id: int, db: AsyncSession = Depends(get_async_session),
                                    user: User = Depends(current_student_user)):
    result = await db.execute(select(HomeworkReview).where(HomeworkReview.id == review_id).
                              options(selectinload(HomeworkReview.submission)))

    review = result.scalar_one_or_none()
    if review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    if user.id != review.submission.student_id and user.role not in (Role.ADMIN, Role.TEACHER):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='You are not allowed')
    return review


async def get_review_or_none(review_id, db, user):
    result = await db.execute(select(HomeworkReview).where(HomeworkReview.id == review_id).
                              options(selectinload(HomeworkReview.submission).selectinload(HomeworkSubmission.homework)
                                      .selectinload(Homework.lesson)))
    review = result.scalar_one_or_none()
    if review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    if user.id != review.submission.homework.lesson.teacher_id and user.role != Role.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='You are not allowed')
    return review


@homework_review_router.patch('/{review_id}', response_model=HomeworkReviewRead, status_code=status.HTTP_200_OK)
async def update_homework_review(review_id: int, data: HomeworkReviewUpdate,
                                 db: AsyncSession = Depends(get_async_session),
                                 user: User = Depends(current_teacher_user)):
    review = await get_review_or_none(review_id, db, user)
    new_data = data.model_dump(exclude_unset=True)
    for key, value in new_data.items():
        setattr(review, key, value)
    await db.commit()
    await db.refresh(review)
    return review


@homework_review_router.delete('/{review_id}', status_code=status.HTTP_200_OK)
async def destroy_homework_review(review_id: int, db: AsyncSession = Depends(get_async_session),
                                  user: User = Depends(current_teacher_user)):
    review = await get_review_or_none(review_id, db, user)
    await db.delete(review)
    await db.commit()
    return {'detail': f"Review with id {review_id} has been deleted"}
