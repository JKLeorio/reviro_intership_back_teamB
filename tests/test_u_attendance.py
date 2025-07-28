# from datetime import time, timedelta
# from fastapi import status
# import pytest

# from db.types import AttendanceStatus
# from tests.utils import dict_comparator
# from utils.date_time_utils import get_current_time 

# CLASSROOM_DATA = {
#     'name': 'BIG_CHUNGUS ROOM 5'
# }

# LEVEL_DATA = {
#     'code': 'J4',
#     'description': 'Big Chungus'
# }

# LANGUAGE_DATA = {
#     'name': 'test5_language'
# }

# COURSE_DATA = {
#     'name': 'English',
#     'price': 123,
#     'description': 'best course',
#     'language_id': None,
#     'level_id': None,
# }

# USER_DATA = {
#     'first_name': 'test',
#     'last_name': 'chungus',
#     'phone_number': '9955555555555',
#     'email': 'user@uuser.com',
#     'hashed_password': '12324242',
#     'role': 'teacher'
# }

# GROUP_DATA = {
#     'name': 'group attendance',
#     'start_date': get_current_time().date(),
#     'end_date': get_current_time().date() + timedelta(days=30),
#     'is_active': False,
#     'is_archived': False,
#     'course_id': None,
#     'teacher_id': None,
# }

# LESSON_DATA = {
#     'name': 'lesson attendance',
#     'description' : 'description attendance',
#     'link': 'http://127.0.0.1:8000',
#     "day": get_current_time().date(),
#     "lesson_start": time(hour=9, minute=0), 
#     "lesson_end": time(hour=11, minute=15), 
#     "teacher_id": None, 
#     "group_id": None,
#     "classroom_id": None
# }


# group_url = '/group/'
# group_student_url = '/group-students/'



# ATTENDANCE_CREATE = {
#     'status' : AttendanceStatus.ABSENT.value,
#     'student_id': None,
#     'lesson_id': None
# }

# ATTENDANCE_UPDATE = {
#     'status' : AttendanceStatus.ATTENTED.value,
#     'student_id': None,
#     'lesson_id': None
# }

# ATTENDANCE_PARTIAL_UPDATE = {
#     'status' : AttendanceStatus.ATTENTED.value,
#     'student_id': None,
#     'lesson_id': None
# }

# STUDENT_ID = None

# @pytest.mark.anyio
# async def test_set_up(
#     client,
#     course_factory, 
#     level_factory, 
#     language_factory, 
#     user_factory,
#     group_factory,
#     lesson_factory,
#     classroom_factory
#     ):
#     classroom_id = await classroom_factory(CLASSROOM_DATA)
#     level_id= await level_factory(LEVEL_DATA)
#     language_id= await language_factory(LANGUAGE_DATA)
#     teacher_id = await user_factory(USER_DATA)
#     USER_DATA['email'] = 'user_student55@user.com'
#     USER_DATA['role'] = 'student'
#     USER_DATA['phone_number'] = '555555555554444'
#     student_id = await user_factory(USER_DATA)
#     STUDENT_ID = student_id
#     COURSE_DATA['level_id'] = level_id
#     COURSE_DATA['language_id'] = language_id
#     course_id = await course_factory(COURSE_DATA)
#     GROUP_DATA['course_id'] = course_id
#     GROUP_DATA['teacher_id'] = teacher_id
#     group_id = await group_factory(GROUP_DATA)
#     LESSON_DATA['group_id'] = group_id
#     LESSON_DATA['classroom_id'] = classroom_id
#     LESSON_DATA['teacher_id'] = teacher_id
#     lesson = (await lesson_factory(LESSON_DATA))
#     lesson_id = lesson.id
#     LESSON_DATA.update(dict(lesson))
#     LESSON_DATA['day'] = LESSON_DATA['day'].isoformat()
#     LESSON_DATA['lesson_start'] = LESSON_DATA['lesson_start'].isoformat()
#     LESSON_DATA['lesson_end'] = LESSON_DATA['lesson_end'].isoformat()
#     LESSON_DATA['link'] = str(LESSON_DATA['link'])
#     ATTENDANCE_UPDATE['lesson_id'] = lesson_id
#     ATTENDANCE_UPDATE['student_id'] = student_id


# @pytest.mark.anyio
# @pytest.mark.role("teacher")
# async def test_attendance_by_user(client):
#     response = await client.patch(
#         f"/group-students/{LESSON_DATA['group_id']}",
#         json={'students':[STUDENT_ID]}
#         )
#     assert response.status_code == status.HTTP_200_OK
#     response = await client.get(f'/attendance/user/{GROUP_DATA['students'][0]}')
#     assert response.status_code == status.HTTP_200_OK
#     data = response.json()
#     assert isinstance(data['attendance_groups'], list)
#     for attendance_group in data['attendance_groups']:
#         if attendance_group:
#             group = attendance_group.get('group', None)
#             if (group is not None) and group['id'] == LESSON_DATA['group_id']:
#                 buff = {
#                     'name':GROUP_DATA['name'],
#                     }
#                 dict_comparator(buff, group)
#                 assert bool(attendance_group['attendance']) == True

# @pytest.mark.anyio
# @pytest.mark.role("teacher")
# async def test_attendance_by_lesson(client):
#     response = await client.get(f"/attendance/lesson/{ATTENDANCE_UPDATE['lesson_id']}")
#     assert response.status_code == status.HTTP_200_OK
#     data = response.json()
#     assert isinstance(data, list)
#     assert bool(data) == True
