import pytest


@pytest.mark.anyio
async def test_create_classroom(client):
    response = await client.post('/classrooms/', json={"name": "London"})
    assert response.status_code == 201
    assert response.json()['name'] == 'London'


@pytest.mark.anyio
@pytest.mark.role("teacher")
async def test_create_classroom_by_non_admin(client):
    response = await client.post("/classrooms/", json={"name": "Berlin"})
    assert response.status_code == 403
    assert response.json()["detail"] == "You don't have enough permissions"


@pytest.mark.anyio
async def test_get_classrooms(client):
    response = await client.get('/classrooms/')
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.anyio
async def test_get_classroom(client):
    class_response = await client.post("/classrooms/", json={"name": "Madrid"})
    assert class_response.status_code == 201
    classroom_id = class_response.json()["id"]

    response = await client.get(f"/classrooms/{classroom_id}")
    assert response.status_code == 200
    assert response.json()["name"] == class_response.json()["name"]


@pytest.mark.anyio
async def test_update_classroom(client):
    class_response = await client.post("/classrooms/", json={"name": "Barselona"})
    assert class_response.status_code == 201
    classroom_id = class_response.json()['id']

    response = await client.patch(f"/classrooms/{classroom_id}", json={"name": "Barcelona"})
    assert response.status_code == 200
    assert response.json()['name'] == "Barcelona"
    assert response.json()['id'] == classroom_id


@pytest.mark.anyio
@pytest.mark.role("student")
async def test_update_classroom(client):

    response = await client.patch(f"/classrooms/1", json={"name": "Barcelona"})
    assert response.status_code == 403
    assert response.json()['detail'] == "You don't have enough permissions"


@pytest.mark.anyio
async def test_destroy_classroom(client):
    class_response = await client.post("/classrooms/", json={"name": "Tehran"})
    assert class_response.status_code == 201
    classroom_id = class_response.json()['id']

    response = await client.delete(f"/classrooms/{classroom_id}")
    assert response.status_code == 200
    assert response.json()['detail'] == f"Classroom with id {classroom_id} has been deleted"


@pytest.mark.anyio
@pytest.mark.role('student')
async def test_destroy_classroom_by_non_admin(client):
    response = await client.delete(f"/classrooms/2")
    assert response.status_code == 403
    assert response.json()['detail'] == "You don't have enough permissions"


@pytest.mark.anyio
async def test_register_user_success(client):
    new_user = {
        "email": "newstudent@example.com",
        "first_name": "Test",
        "last_name": "Student",
        "role": "student",
    }

    response = await client.post("/auth/register-user", json=new_user)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == new_user["email"]

    lang_resp = await client.post('/languages/', json={'name': "Polish"})
    assert lang_resp.status_code == 201
    language_name = lang_resp.json()["name"]

    level_resp = await client.post('/levels/', json={"code": "C2.1", "description": "Advanced"})
    assert level_resp.status_code == 201
    level_code = level_resp.json()["code"]

    course_data = {"name": "Polish C2.1", "price": 5000, "description": "Italian for advanced",
                   "language_name": language_name, "level_code": level_code}


    course_resp = await client.post('/courses/', json=course_data)
    assert course_resp.status_code == 201
    course_json = course_resp.json()
    assert course_json["name"] == course_data["name"]
    assert course_json["price"] == course_data["price"]
    assert course_json["description"] == course_data["description"]
    assert course_json["language_name"] == language_name
    assert course_json["level_code"] == level_code

    group_data = {
        "name": "Group A",
        "start_date": "2025-06-06",
        "end_date": "2025-09-06",
        "is_active": True,
        "is_archived": False,
        "course_id": course_json['id'],
        "teacher_id": data['id']

    }
    response = await client.post('/group/', json=group_data)
    assert response.status_code == 201
    group_id = response.json()['id']
