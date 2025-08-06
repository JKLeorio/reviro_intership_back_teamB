import pytest
from fastapi import status

from db.types import Role
from models.user import User
from tests.fixtures.factories.schemas.lesson_schema_data_factory import LessonCreateDataFactory
from tests.utils import get_objects_by_ids

base_url = '/attendance/'

@pytest.mark.anyio
@pytest.mark.role("teacher")
async def test_attendance_create(
    client,
    session,
    modern_classroom_factory,
    modern_lesson_factory,
    modern_group_factory,
    modern_user_factory,
    users,
    ):
    students_count = 10
    classroom = await modern_classroom_factory(
        name='404'
    )
    students_validated = await modern_user_factory(
        students_count, 
        role=Role.STUDENT
        )
    students = await get_objects_by_ids(
        session, 
        User, 
        [student.id for student in students_validated]
        )
    group = await modern_group_factory(
        is_active=True,
        is_archived=False,
        students=students
        )
    lesson_create_data = LessonCreateDataFactory.build(
        teacher_id = users['teacher'].id,
        classroom_id = classroom.id
    )

    response_lesson_create = await client.post(
        f"lessons/group/{group.id}",
        json = lesson_create_data
        )
    
    assert response_lesson_create.status_code == status.HTTP_201_CREATED
    lesson_id = response_lesson_create.json()['id']
    response = await client.get(f"{base_url}lesson/{lesson_id}")
    assert response.status_code == status.HTTP_200_OK
    attendance_list = response.json()
    assert isinstance(attendance_list, list)
    assert len(attendance_list) == students_count


