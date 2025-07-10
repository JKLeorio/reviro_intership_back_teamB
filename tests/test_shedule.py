import calendar
from collections import defaultdict
from datetime import date, time, timedelta
from fastapi import status
import pytest

from tests.utils import dict_comparator
from utils.date_time_utils import get_current_time

LEVEL_DATA = {
    'code': 'J10',
    'description': 'Big Chungus'
}

LANGUAGE_DATA = {
    'name': 'test10_language'
}

CLASSROOM_DATA = {
    'name': 'BIG_CHUNGUS ROOM'
}

COURSE_DATA = {
    'name': 'English',
    'price': 123,
    'description': 'best course',
    'language_id': None,
    'level_id': None,
}

USER_DATA = {
    'first_name': 'big',
    'last_name': 'chungus',
    'phone_number': '9951111111111',
    'email': 'user@4user.com',
    'hashed_password': '12324242',
    'role': 'teacher'
}

GROUP_DATA = {
    'name': 'group 1',
    # 'start_date': '2025-07-02',
    # 'end_date': '2025-08-02',
    'start_date': date(year=2025, month=7, day=2),
    'end_date': date(year=2025, month=8, day=2),
    'is_active': False,
    'is_archived': False,
    'course_id': None,
    'teacher_id': None,
    'students': None
}


LESSON_DATA = {
    "name": "To be", 
    "description": "How to use verb to be",
    "link": "https://example.com/", 
    # "day": "2025-07-06",
    # "lesson_start": "09:00", 
    # "lesson_end": "11:15", 
    "day": date(year=2025, month=7, day=6),
    "lesson_start": time(hour=9, minute=0), 
    "lesson_end": time(hour=11, minute=15), 
    "teacher_id": None, 
    "group_id": None,
    "classroom_id": None
}


SHEDULE_RESPONSE = {calendar.day_abbr[day_id].upper() : list()  for day_id in range(7)}



@pytest.mark.anyio
async def test_set_up(
    level_factory,
    classroom_factory,
    language_factory,
    lesson_factory, 
    user_factory,
    group_factory,
    course_factory
):
    level_id = await level_factory(LEVEL_DATA)
    classroom_id = await classroom_factory(CLASSROOM_DATA)
    language_id = await language_factory(LANGUAGE_DATA)
    COURSE_DATA['level_id'] = level_id
    COURSE_DATA['language_id'] = language_id
    teacher_id = await user_factory(USER_DATA)
    USER_DATA['email'] = 'user_user@mail.com'
    USER_DATA['role'] = 'student'
    USER_DATA['phone_number'] = '53453534533423'
    student_id = await user_factory(USER_DATA)
    course_id = await course_factory(COURSE_DATA)
    GROUP_DATA['course_id'] = course_id
    GROUP_DATA['teacher_id'] = teacher_id
    # GROUP_DATA['students'] = [student_id]
    GROUP_DATA['students'] = []
    group_id = await group_factory(GROUP_DATA)
    LESSON_DATA['teacher_id'] = teacher_id
    LESSON_DATA['group_id'] = group_id
    LESSON_DATA['classroom_id'] = classroom_id
    current_time = get_current_time()
    week_start = current_time - timedelta(days=current_time.weekday())
    for day in range(7):
        LESSON_DATA['day'] = week_start + timedelta(days=day)
        lesson = await lesson_factory(LESSON_DATA)
        week_day = calendar.day_abbr[day].upper()
        SHEDULE_RESPONSE[week_day].append(
            {
                'group': {
                    'id': LESSON_DATA['group_id']
                },
                'lessons': [lesson]
            }
        )

@pytest.mark.anyio
@pytest.mark.role('student')
async def test_shedule_global(client):
    response = await client.get('/shedule/')
    assert response.status_code == status.HTTP_200_OK