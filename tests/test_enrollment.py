import pytest
from fastapi import status

from tests.utils import dict_comparator
from models.course import Course, Language, Level




LEVEL_DATA = {
    'code': 'B3',
    'description': 'Big Chungus'
}

LANGUAGE_DATA = {
    'name': 'test_language'
}

#Data используется для прямого создания через модель
COURSE_DATA = {
    'name': 'English',
    'price': 123,
    'description': 'best course',
    'language_id': None,
    'level_id': None,
}

#Create,update и т.д используется для API
ENROLLMENT_CREATE = {
    "first_name": "ivan",
    "last_name": "popov",
    "email": "test@test.com",
    "phone_number": "996555555555",
    "course_id": None
}

ENROLLMENT_UPDATE = {
    'first_name': 'ichigo',
    'last_name': 'kurasaki',
    'email': 'test@changed.com',
    'phone_number': '996444444444',
    'course_id': None
}

ENROLLMENT_PARTIAL_UPDATE = {
    'first_name': 'big',
    'last_name': 'chungus'
}


@pytest.mark.anyio
async def test_set_up(course_factory, level_factory, language_factory):

    level_id= await level_factory(LEVEL_DATA)
    language_id= await language_factory(LANGUAGE_DATA)
    COURSE_DATA['level_id'] = level_id
    COURSE_DATA['language_id'] = language_id
    course_id = await course_factory(COURSE_DATA)
    ENROLLMENT_CREATE['course_id'] = course_id
    ENROLLMENT_UPDATE['course_id'] = course_id


@pytest.mark.anyio
async def test_create_enrollment(client):
    response = await client.post('/enrollment/', json=ENROLLMENT_CREATE)
    print(response.json())
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    dict_comparator(ENROLLMENT_CREATE, data)



@pytest.mark.anyio
async def test_enrollment_list(client):
    response = await client.get('/enrollment/')
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    isinstance(data, list)


@pytest.mark.anyio
async def test_enrollment_detail(client):
    enrollment_current = await client.post('/enrollment/', json=ENROLLMENT_CREATE)
    assert enrollment_current.status_code == status.HTTP_201_CREATED
    response = await client.get(f"/enrollment/{enrollment_current.json().get('id', 0)}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    dict_comparator(ENROLLMENT_CREATE, data)



@pytest.mark.anyio
async def test_enrollment_update(client):
    enrollment_current = await client.post('/enrollment/', json=ENROLLMENT_CREATE)
    assert enrollment_current.status_code == status.HTTP_201_CREATED
    response = await client.put(
        f"/enrollment/{enrollment_current.json().get('id', 0)}",
        json=ENROLLMENT_UPDATE)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    dict_comparator(ENROLLMENT_UPDATE, data)
    enrollment_current = data



@pytest.mark.anyio
async def test_enrollment_partial_update(client):
    enrollment_current = await client.post('/enrollment/', json=ENROLLMENT_CREATE)
    assert enrollment_current.status_code == status.HTTP_201_CREATED
    response = await client.patch(
        f"/enrollment/{enrollment_current.json().get('id', 0)}",
        json=ENROLLMENT_PARTIAL_UPDATE)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    dict_comparator(ENROLLMENT_PARTIAL_UPDATE, data)


@pytest.mark.anyio
async def test_enrollment_delete(client):
    enrollment_current = await client.post('/enrollment/', json=ENROLLMENT_CREATE)
    assert enrollment_current.status_code == status.HTTP_201_CREATED
    response = await client.delete(
        f"/enrollment/{enrollment_current.json().get('id', 0)}"
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
    response_detail = await client.delete(
        f"/enrollment/{enrollment_current.json().get('id', 0)}"
    )
    assert response_detail.status_code == status.HTTP_404_NOT_FOUND



@pytest.mark.anyio
@pytest.mark.role('student')
async def test_enrollment_list_permission(client):
    response = await client.get('/enrollment/')
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.anyio
@pytest.mark.role('student')
async def test_enrollment_update_permission(client):
    enrollment_create_resp = await client.post('/enrollment/', json=ENROLLMENT_CREATE)
    assert enrollment_create_resp.status_code == status.HTTP_201_CREATED
    enrollment_id = enrollment_create_resp.json()['id']
    response = await client.put(f'/enrollment/{enrollment_id}', json=ENROLLMENT_UPDATE)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.anyio
@pytest.mark.role('student')
async def test_enrollment_part_update_permission(client):
    enrollment_create_resp = await client.post('/enrollment/', json=ENROLLMENT_CREATE)
    assert enrollment_create_resp.status_code == status.HTTP_201_CREATED
    enrollment_id = enrollment_create_resp.json()['id']
    response = await client.patch(
        f'/enrollment/{enrollment_id}', 
        json=ENROLLMENT_PARTIAL_UPDATE
        )
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.anyio
@pytest.mark.role('student')
async def test_enrollment_delete_permission(client):
    enrollment_create_resp = await client.post('/enrollment/', json=ENROLLMENT_CREATE)
    assert enrollment_create_resp.status_code == status.HTTP_201_CREATED
    enrollment_id = enrollment_create_resp.json()['id']
    response = await client.delete(f'/enrollment/{enrollment_id}')
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.anyio
async def test_enrollment_wrong_id(client):
    url = f'/enrollment/{9999}'
    response_detail = await client.get(url)
    assert response_detail.status_code == status.HTTP_404_NOT_FOUND
    response_update = await client.put(url, json=ENROLLMENT_UPDATE)
    assert response_update.status_code == status.HTTP_404_NOT_FOUND
    response_partial_update = await client.patch(url, json=ENROLLMENT_PARTIAL_UPDATE)
    assert response_partial_update.status_code == status.HTTP_404_NOT_FOUND