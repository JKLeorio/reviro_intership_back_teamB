import pytest
from fastapi import status

from db.types import Role
from tests.fixtures.factories.schemas.user_schema_data_factory import StudentRegisterDataFactory, TeacherRegisterDataFactory
from tests.utils import dict_comparator


USER_DATA = {
    'first_name' : 'name',
    'last_name' : 'last_name',
    'email' : '12345@email.com',
    'phone_number': '111111111',
    'role': 'student'
}

@pytest.mark.anyio
async def test_register_user(client, user_factory):
    response = await client.post(
        '/auth/register-user',
        json=USER_DATA
        )
    assert response.status_code == status.HTTP_201_CREATED
    dict_comparator(USER_DATA, response.json())


# @pytest.mark.anyio
# async def test_login(client, user_factory):
#     USER_DATA['email'] = '7@mail.com'
#     USER_DATA['phone_number'] = '999'
#     response_reg = await client.post(
#         '/auth/register-user',
#         json=USER_DATA
#         )
#     assert response_reg.status_code == status.HTTP_201_CREATED
#     data = response_reg.json()
#     response = await client.post(
#         '/auth/login', 
#         data={
#             'username': data['email'],
#             'password': data['password'],
#             }
#         )
#     assert response.status_code == status.HTTP_200_OK
#     data = response.json()
#     assert data['access_token'] is not None



@pytest.mark.anyio
@pytest.mark.role("super_admin")
async def test_register_admin(client):
    USER_DATA['email'] = '8@mail.com'
    USER_DATA['phone_number'] = '888'
    USER_DATA['role'] = 'admin'
    response = await client.post(
        '/auth/register-admin',
        json=USER_DATA
        )
    assert response.status_code == status.HTTP_201_CREATED
    dict_comparator(USER_DATA, response.json())



@pytest.mark.anyio
@pytest.mark.role('student')
async def test_register_admin_permission(client):
    response = await client.post(
        '/auth/register-admin',
        )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.anyio
@pytest.mark.role('student')
async def test_register_user_permission(client):
    response = await client.post(
        '/auth/register-user'
        )
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.anyio
@pytest.mark.role('admin')
async def test_register_student_with_group(
    client,
    modern_group_factory
    ):
    #Временно пока не модифицирую build контроллера для фабрик
    json = StudentRegisterDataFactory.build(
        email='zero@mail.com',
        phone_number='1231324345',
        role=Role.STUDENT
        )
    json['full_name'] = ' '.join((json['full_name'].split()[:2]))
    group = await modern_group_factory()
    group2 = await modern_group_factory()
    params = {
        'group_id' : [group.id, group2.id]
        }
    response = await client.post(
        f'/auth/register-student-with-group', 
        json=json,
        params = params
        )
    assert response.status_code == status.HTTP_201_CREATED, response.text
    data = response.json()
    # assert set(params['group_id']) == ((set(data['group_ids']) & set(params['group_id'])))
    assert isinstance(data['groups'], list)
    dict_comparator(json, data)

@pytest.mark.anyio
@pytest.mark.role('admin')
async def test_register_teacher_with_group(
    client,
    modern_group_factory
    ):
    #Временно пока не модифицирую build контроллера для фабрик
    json : dict = TeacherRegisterDataFactory.build(
        email='one@mail.com',
        phone_number='4234234234',
        role=Role.TEACHER
        )
    json['full_name'] = ' '.join((json['full_name'].split()[:2]))
    group = await modern_group_factory()
    response = await client.post(
        f'/auth/register-teacher-with-group/{group.id}', 
        json=json
        )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data['group_id'] == group.id
    dict_comparator(json, data)
