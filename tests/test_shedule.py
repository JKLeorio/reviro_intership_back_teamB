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

current_time_full = get_current_time()
current_date = current_time_full.date()
current_time = current_time_full.time()
week_start = current_time_full - timedelta(days=current_time_full.weekday())


GROUP_DATA = {
    'name': 'group 1',
    # 'start_date': '2025-07-02',
    # 'end_date': '2025-08-02',
    'start_date': current_date,
    'end_date': current_date + timedelta(days=30),
    'approximate_lesson_start':time(hour=12),
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
    "day": None,
    "lesson_start": time(hour=9, minute=0), 
    "lesson_end": time(hour=11, minute=15), 
    "teacher_id": None, 
    "group_id": None,
    "classroom_id": None
}


SHEDULE_RESPONSE = {calendar.day_abbr[day_id].upper() : list()  for day_id in range(7)}



@pytest.mark.anyio
async def test_set_up(
    client,
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
    response = await client.patch(
        f"/group-students/{group_id}",
        json={'students':[student_id]}
        )
    assert response.status_code == status.HTTP_200_OK
    GROUP_DATA['students'] = [student_id]
    LESSON_DATA['teacher_id'] = teacher_id
    LESSON_DATA['group_id'] = group_id
    LESSON_DATA['classroom_id'] = classroom_id
    for day in range(7):
        LESSON_DATA['day'] = (week_start + timedelta(days=day)).date()
        lesson = await lesson_factory(LESSON_DATA)
        week_day = calendar.day_abbr[day].upper()
        lesson = dict(lesson)
        lesson['day'] = lesson['day'].isoformat()
        lesson['lesson_start'] = lesson['lesson_start'].isoformat()
        lesson['lesson_end'] = lesson['lesson_end'].isoformat()
        lesson['link'] = str(lesson['link'])
        lesson['teacher'] = dict(lesson['teacher'])
        lesson['classroom'] = dict(lesson['classroom'])
        SHEDULE_RESPONSE[week_day].append(
            {
                'group': {
                    'id': LESSON_DATA['group_id']
                },
                'lessons': [lesson]
            }
        )


def compare_shedule_with_result(response):
    data = response.json()
    for day_abbr in calendar.day_abbr:
        week_day = data[day_abbr.upper()]
        if week_day is not None:
            for group_item in week_day:
                group = group_item.get('group', None)
                if group is not None:
                    if group['id'] == LESSON_DATA['group_id']:
                        dict_comparator(SHEDULE_RESPONSE[day_abbr.upper()][0]['group'], group)
                        compare_lesson = SHEDULE_RESPONSE[day_abbr.upper()][0]['lessons'][0]
                        lessons = group_item['lessons']
                        for lesson in lessons:
                            lesson_id = lesson.get('id', None)
                            if lesson_id is not None:
                                if lesson_id == compare_lesson['id']:
                                    dict_comparator(compare_lesson, lesson)
                                    break

@pytest.mark.anyio
@pytest.mark.role('student')
async def test_shedule_global(client):
    response = await client.get('/shedule/')
    assert response.status_code == status.HTTP_200_OK
    compare_shedule_with_result(response)


@pytest.mark.anyio
@pytest.mark.role('teacher')
async def test_shedule_by_group(client):
    response = await client.get('/shedule/group/' + str(LESSON_DATA['group_id']))
    assert response.status_code == status.HTTP_200_OK
    compare_shedule_with_result(response)

@pytest.mark.anyio
@pytest.mark.role('student')
async def test_shedule_user(client):
    response = await client.get('/shedule/my')
    assert response.status_code == status.HTTP_200_OK
