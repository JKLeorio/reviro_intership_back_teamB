import pytest
from httpx import AsyncClient, Response
from fastapi import status

from tests.utils import dict_comparator

LEVEL_DATA = {
    'code': 'J3',
    'description': 'Big Chungus'
}

LANGUAGE_DATA = {
    'name': 'test2_language'
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
    'phone_number': '9954443332222',
    'email': 'user@2user.com',
    'hashed_password': '12324242',
    'role': 'teacher'
}

GROUP_CREATE = {
    'name': 'group 1',
    'start_date': '2025-07-02',
    'end_date': '2025-08-02',
    'is_active': False,
    'is_archived': False,
    'course_id': None,
    'teacher_id': None,
}

GROUP_UPDATE = {
    'name': 'group 2',
    'start_date': '2026-07-02',
    'end_date': '2026-08-02',
    'is_active': True,
    'is_archived': False,
    'course_id': None,
    'teacher_id': None,
}

GROUP_PARTIAL_UPDATE = {
    'name': 'group 3',
    'end_date': '2026-09-02'
}

GROUP_STUDENT_UPDATE = {
    'name': 'group 2',
    'start_date': '2026-07-02',
    'end_date': '2026-08-02',
    'is_active': True,
    'is_archived': False,
    'course_id': None,
    'teacher_id': None,
    'students': None
}

GROUP_STUDENT_PARTIAL_UPDATE = {
    'name': 'group 3',
    'end_date': '2026-09-02',
    'students': None
}

group_url = '/group/'
group_student_url = '/group-students/'


@pytest.mark.anyio
async def test_set_up(
    course_factory, 
    level_factory, 
    language_factory, 
    user_factory
    ):

    level_id= await level_factory(LEVEL_DATA)
    language_id= await language_factory(LANGUAGE_DATA)
    user_id = await user_factory(USER_DATA)
    USER_DATA['email'] = 'user_student@user.com'
    USER_DATA['role'] = 'student'
    USER_DATA['phone_number'] = '345345434534'
    student_id = await user_factory(USER_DATA)
    COURSE_DATA['level_id'] = int(level_id)
    COURSE_DATA['language_id'] = int(language_id)
    course_id = await course_factory(COURSE_DATA)
    GROUP_CREATE['course_id'] = int(course_id)
    GROUP_UPDATE['course_id'] = int(course_id)
    GROUP_CREATE['teacher_id'] = int(user_id)
    GROUP_UPDATE['teacher_id'] = int(user_id)
    GROUP_STUDENT_UPDATE['course_id'] = int(course_id)
    GROUP_STUDENT_UPDATE['teacher_id'] = int(user_id)
    GROUP_STUDENT_UPDATE['students'] = [int(student_id)]
    GROUP_STUDENT_PARTIAL_UPDATE['students'] = [int(student_id)]
    


async def create_group(client: AsyncClient) -> Response:
    response = await client.post(group_url, json=GROUP_CREATE)
    assert response.status_code == status.HTTP_201_CREATED
    return response

@pytest.mark.anyio
async def test_group_list(client):
    response = await client.get(group_url)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)

@pytest.mark.anyio
async def test_group_create(client):
    group_resp = await create_group(client)
    data = group_resp.json()
    dict_comparator(GROUP_CREATE, data)
    

@pytest.mark.anyio
async def test_group_detail(client):
    group_resp = await create_group(client)
    group_id = group_resp.json()['id']
    response = await client.get(group_url+str(group_id))
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    dict_comparator(GROUP_CREATE, data)

@pytest.mark.anyio
async def test_group_update(client):
    group_resp = await create_group(client)
    group_id = group_resp.json()['id']
    response: Response = await client.put(
        group_url+str(group_id), 
        json=GROUP_UPDATE
        )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    dict_comparator(GROUP_UPDATE, data)

@pytest.mark.anyio
async def test_group_partial_update(client):
    group_resp = await create_group(client)
    group_id = group_resp.json()['id']
    response = await client.patch(
        group_url+str(group_id), 
        json=GROUP_PARTIAL_UPDATE
        )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    dict_comparator({**GROUP_CREATE,**GROUP_PARTIAL_UPDATE}, data)

@pytest.mark.anyio
async def test_group_delete(client):
    group_resp = await create_group(client)
    group_id = group_resp.json()['id']
    response = await client.delete(group_url+str(group_id))
    assert response.status_code == status.HTTP_204_NO_CONTENT
    group_detail = await client.get(group_url+str(group_id))
    assert group_detail.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.anyio
async def test_group_student_list(client):
    response = await client.get(group_student_url)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.anyio
async def test_group_student_detail(client):
    group_resp = await create_group(client)
    group_id = group_resp.json()['id']
    response = await client.get(group_student_url+str(group_id))
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    dict_comparator(GROUP_CREATE, data)

@pytest.mark.anyio
async def test_group_student_update(client):
    group_resp = await create_group(client)
    group_id = group_resp.json()['id']
    response = await client.put(
        group_student_url+str(group_id),
        json=GROUP_STUDENT_UPDATE
        )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    buff = {**GROUP_STUDENT_UPDATE}
    buff.pop('students')
    dict_comparator(buff, data)

@pytest.mark.anyio
async def test_group_student_partial_update(client):
    group_resp = await create_group(client)
    group_id = group_resp.json()['id']
    response = await client.patch(
        group_student_url+str(group_id), 
        json=GROUP_STUDENT_PARTIAL_UPDATE
        )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    buff = {**GROUP_STUDENT_PARTIAL_UPDATE}
    buff.pop('students')
    dict_comparator({**GROUP_CREATE, **buff}, data)


@pytest.mark.anyio
@pytest.mark.role('student')
async def test_group_student_list_permission(client):
    response = await client.get(
        group_student_url
        )
    assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.anyio
@pytest.mark.role('student')
async def test_group_student_detail_permission(client):
    response = await client.get(
        group_student_url+'1'
        )
    assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.anyio
@pytest.mark.role('student')
async def test_group_student_partial_update_permission(client):
    response = await client.patch(
        group_student_url+'0', 
        json=GROUP_STUDENT_PARTIAL_UPDATE
        )
    assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.anyio
@pytest.mark.role('student')
async def test_group_student_update_permission(client):
    response = await client.put(
        group_student_url+'0', 
        json=GROUP_STUDENT_UPDATE
        )
    assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.anyio
@pytest.mark.role('student')
async def test_group_create_permission(client):
    response = await client.post(group_url, json=GROUP_CREATE)
    assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.anyio
@pytest.mark.role('student')
async def test_group_update_permission(client):
    response = await client.put(group_url+'0', json=GROUP_UPDATE)
    assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.anyio
@pytest.mark.role('student')
async def test_group_partial_update_permission(client):
    response = await client.patch(group_url+'0', json=GROUP_PARTIAL_UPDATE)
    assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.anyio
@pytest.mark.role('student')
async def test_group_delete_permission(client):
    response = await client.delete(group_url+'0')
    assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.anyio
async def test_group_profile(client):
    response = await client.get(group_url+'my')
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert bool(data)