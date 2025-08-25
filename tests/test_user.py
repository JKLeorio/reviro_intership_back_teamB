import pytest

from fastapi import status
from sqlalchemy.orm import selectinload
from db.types import Role
from models.group import Group
from models.user import User
from tests.utils import dict_comparator

USER_DATA = {
    'first_name':'big',
    'last_name':'chungus',
    'email':'1@mail.com',
    'phone_number':'12345',
    'role': 'student',
    'hashed_password':'dsafbsabdf'
}


@pytest.mark.anyio
async def test_user_list(client, user_factory):
    user_id = await user_factory(USER_DATA)
    response = await client.get('/user/')
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    buff = {**USER_DATA}
    buff.pop('hashed_password')
    for user_item in data:
        user_item_id = user_item.get('id', None)
        if user_item_id is not None and user_id == user_item_id:
            dict_comparator(buff, user_item)

@pytest.mark.anyio
async def test_user_detail(client, user_factory):
    USER_DATA['email'] = '2@mail.com'
    USER_DATA['phone_number'] = '123'
    user_id = await user_factory(USER_DATA)
    response = await client.get(f'/user/{user_id}')
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    buff = {**USER_DATA}
    buff.pop('hashed_password')
    dict_comparator(buff, data)

@pytest.mark.anyio
async def test_user_update(client, user_factory):
    USER_DATA['email'] = '3@mail.com'
    USER_DATA['phone_number'] = '1234'
    user_id = await user_factory(USER_DATA)
    USER_DATA['email'] = "710@mail.com"
    USER_DATA['phone_number'] = '7775'
    USER_DATA['first_name'] = 'biba'
    USER_DATA['last_name'] = 'boba'
    response = await client.put(f'/user/{user_id}', json=USER_DATA)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    buff = {**USER_DATA}
    buff.pop('hashed_password')
    dict_comparator(buff, data)

@pytest.mark.anyio
async def test_user_partial_update(client, user_factory):
    USER_DATA['email'] = '4@mail.com'
    USER_DATA['phone_number'] = '333'
    user_id = await user_factory(USER_DATA)
    USER_DATA['email'] = "6@mail.com"
    USER_DATA['phone_number'] = '777'
    response = await client.put(f'/user/{user_id}', json=USER_DATA)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    buff = {**USER_DATA}
    buff.pop('hashed_password')
    dict_comparator(buff, data)

@pytest.mark.anyio
async def test_user_delete(client, user_factory):
    USER_DATA['email'] = '5@mail.com'
    USER_DATA['phone_number'] = '555'
    user_id = await user_factory(USER_DATA)
    response = await client.delete(f'/user/{user_id}')
    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.anyio
async def test_student_list(
    client,
    modern_group_factory,
    modern_user_factory,
    session
):
    student_id = (await modern_user_factory(role=Role.STUDENT)).id
    group_id = (await modern_group_factory()).id
    group = await session.get(
        Group,
        group_id
    )
    student = await session.get(
        User,
        student_id,
    )
    await session.refresh(group, attribute_names=['students'])
    group.students.append = student
    await session.commit()
    response = await client.get("/user/students")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data['students'], list)
    assert isinstance(data['pagination'], dict)

@pytest.mark.anyio
async def test_teacher_list(
    client,
    modern_group_factory,
    modern_user_factory
):
    group = await modern_group_factory()
    response = await client.get("/user/teachers")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data['teachers'], list)
    assert isinstance(data['pagination'], dict)


@pytest.mark.anyio
async def test_teacher_update(
    client,
    modern_user_factory
):
    user = await modern_user_factory(role=Role.TEACHER)
    json = {
        'email': 'up1email@mail.com',
        'phone_number': '1111111111143243'
    }
    response = await client.patch(f"/user/teacher/{user.id}", json=json)
    assert response.status_code == status.HTTP_200_OK

@pytest.mark.anyio
async def test_student_update(
    client,
    modern_user_factory
):
    user = await modern_user_factory(role=Role.STUDENT)
    json = {
        'email': 'up22email@mail.com',
        'phone_number': '11111111113243'
    }
    response = await client.patch(f"/user/student/{user.id}", json=json)
    assert response.status_code == status.HTTP_200_OK