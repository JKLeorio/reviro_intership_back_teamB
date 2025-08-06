import pytest
from fastapi import status

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


@pytest.mark.anyio
async def test_login(client, user_factory):
    USER_DATA['email'] = '7@mail.com'
    USER_DATA['phone_number'] = '999'
    response_reg = await client.post(
        '/auth/register-user',
        json=USER_DATA
        )
    assert response_reg.status_code == status.HTTP_201_CREATED
    data = response_reg.json()
    response = await client.post(
        '/auth/login', 
        data={
            'username': data['email'],
            'password': data['password'],
            }
        )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['access_token'] is not None



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