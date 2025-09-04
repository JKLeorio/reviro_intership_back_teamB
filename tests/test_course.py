import pytest


@pytest.mark.anyio
async def test_create_language(client):
    response = await client.post("/languages/", json={"name": "English"})
    assert response.status_code == 201
    assert response.json()["name"] == "English"


@pytest.mark.anyio
@pytest.mark.role("student")
async def test_create_language_student(client):
    response = await client.post('/languages/', json={"name": "French"})
    assert response.status_code == 403
    assert response.json()["detail"] == "You don't have enough permissions"


@pytest.mark.anyio
async def test_get_languages(client):
    response = await client.get("/languages/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.anyio
async def test_get_language(client):
    create_resp = await client.post("/languages/", json={"name": "Chinese"})
    assert create_resp.status_code == 201
    lang_id = create_resp.json()["id"]

    response = await client.get(f"/languages/{lang_id}")
    assert response.status_code == 200
    data = response.json()

    assert data["id"] == lang_id
    assert data["name"] == "Chinese"



@pytest.mark.anyio
async def test_update_language(client):
    response = await client.post("/languages/", json={"name": "Old Name"})
    assert response.status_code == 201
    lang_id = response.json()["id"]

    response = await client.patch(f"/languages/{lang_id}", json={"name": "German"})
    assert response.json()["id"] == lang_id
    assert response.json()["name"] == "German"


@pytest.mark.anyio
@pytest.mark.role("student")
async def test_update_language_by_student(client):

    response = await client.patch(f"/languages/1", json={"name": "Spanish"})
    assert response.status_code == 403
    assert response.json()["detail"] == "You don't have enough permissions"


@pytest.mark.anyio
async def test_destroy_language(client):
    response = await client.post("/languages/", json={"name": "Turkish"})
    assert response.status_code == 201
    lang_id = response.json()["id"]

    response = await client.delete(f"/languages/{lang_id}")
    assert response.status_code == 200


@pytest.mark.anyio
@pytest.mark.role("teacher")
async def test_destroy_language_by_teacher(client):
    response = await client.delete("/languages/1")
    assert response.status_code == 403
    assert response.json()["detail"] == "You don't have enough permissions"


@pytest.mark.anyio
async def test_create_level(client):
    response = await client.post('/levels/', json={"code": "a1", "description": "Beginner level"})
    assert response.status_code == 201
    assert response.json()['code'] == 'A1'
    assert response.json()["description"] == "Beginner level"


@pytest.mark.anyio
@pytest.mark.role("teacher")
async def test_create_level_by_non_admin_user(client):
    response = await client.post("/levels/", json={"code": "b1", "description": "Intermediate"})
    assert response.status_code == 403
    assert response.json()['detail'] == "You don't have enough permissions"


@pytest.mark.anyio
async def test_get_levels(client):
    response = await client.get("/levels/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.anyio
async def test_get_level(client):
    response = await client.post('/levels/', json={"code": "A2", "description": "Beginner plus"})
    assert response.status_code == 201
    level_id = response.json()["id"]

    response = await client.get(f"/levels/{level_id}")
    assert response.status_code == 200
    data = response.json()
    assert data['id'] == level_id
    assert data["description"] == "Beginner plus"


@pytest.mark.anyio
async def test_update_level(client):
    response = await client.post('/levels/', json={"code": 'c1.1', "description": "Fluent"})
    assert response.status_code == 201
    level_id = response.json()["id"]

    response = await client.patch(f'/levels/{level_id}', json={"code": "c1"})
    assert response.status_code == 200
    assert response.json()["code"] == "C1"
    assert response.json()["description"] == "Fluent"


@pytest.mark.anyio
@pytest.mark.role("teacher")
async def test_update_level_by_non_admin_user(client):
    response = await client.patch('/levels/2', json={"description": "jaselfjsl"})
    assert response.status_code == 403
    assert response.json()["detail"] == "You don't have enough permissions"


@pytest.mark.anyio
async def test_destroy_level(client):
    response = await client.post('/levels/', json={"code": "code", "description": "description"})
    assert response.status_code == 201
    level_id = response.json()["id"]

    response = await client.delete(f"/levels/{level_id}")
    assert response.status_code == 200


@pytest.mark.anyio
async def test_create_course(client):
    lang_resp = await client.post('/languages/', json={'name': "Italian"})
    assert lang_resp.status_code == 201
    language_name = lang_resp.json()["name"]

    level_resp = await client.post('/levels/', json={"code": "C2", "description": "Advanced"})
    assert level_resp.status_code == 201
    level_code = level_resp.json()["code"]

    course_data = {"name": "Italian C2", "price": 5000, "description": "Italian for advanced",
                   "language_name": language_name, "level_code": level_code}

    course_resp = await client.post('/courses/', json=course_data)
    assert course_resp.status_code == 201
    course_json = course_resp.json()
    assert course_json["name"] == course_data["name"]
    assert course_json["price"] == course_data["price"]
    assert course_json["description"] == course_data["description"]
    assert course_json["language_name"] == language_name
    assert course_json["level_code"] == level_code


@pytest.mark.anyio
@pytest.mark.role("student")
async def test_create_course_by_non_admin_user(client):

    course_data = {"name": "Italian C2", "price": 5000, "description": "Italian for advanced",
                   "language_name": "Italian", "level_code": "C2"}

    course_resp = await client.post('/courses/', json=course_data)
    assert course_resp.status_code == 403


@pytest.mark.anyio
async def test_get_courses(client):
    response = await client.get("/courses/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.anyio
@pytest.mark.role("teacher")
async def test_get_courses_by_non_admin_user(client):
    response = await client.get("/courses/")
    assert response.status_code == 403
    # assert isinstance(response.json(), list)


@pytest.mark.anyio
async def test_get_course(client):
    level_resp = await client.post('/levels/', json={"code": "B1", "description": "Intermediate"})
    assert level_resp.status_code == 201
    level_code = level_resp.json()["code"]

    lang_resp = await client.post('/languages/', json={'name': "Korean"})
    assert lang_resp.status_code == 201
    language_name = lang_resp.json()["name"]

    course_data = {"name": "Korean B1", "price": 5000, "description": "Korean for intermediate",
                   "language_name": language_name, "level_code": level_code}

    course_resp = await client.post('/courses/', json=course_data)
    assert course_resp.status_code == 201
    course_json = course_resp.json()
    course_id = course_json['id']

    response = await client.get(f"/courses/{course_id}")
    assert response.status_code == 200
    assert response.json()["name"] == course_data['name']


@pytest.mark.anyio
async def test_update_course(client):
    level_resp = await client.post('/levels/', json={"code": "B2", "description": "Upper Intermediate"})
    assert level_resp.status_code == 201
    level_code = level_resp.json()["code"]

    lang_resp = await client.post('/languages/', json={'name': "Russian"})
    assert lang_resp.status_code == 201
    language_name = lang_resp.json()["name"]

    course_data = {"name": "Russian B2", "price": 5000, "description": "Russian for intermediate",
                   "language_name": language_name, "level_code": level_code}

    course_resp = await client.post('/courses/', json=course_data)
    assert course_resp.status_code == 201
    course_json = course_resp.json()
    course_id = course_json['id']

    update_level_resp = await client.post('/levels/', json={"code": "B1.1", "description": "Upper Intermediate"})
    assert update_level_resp.status_code == 201
    update_level_id = update_level_resp.json()['id']

    response = await client.patch(f"/courses/{course_id}", json={"level_id": update_level_id})
    assert response.status_code == 200
    assert response.json()['name'] == course_data['name']
    assert response.json()['level_id'] == update_level_id


@pytest.mark.anyio
async def test_destroy_course(client):
    response = await client.delete('/courses/2')
    assert response.status_code == 200


@pytest.mark.anyio
@pytest.mark.role("student")
async def test_destroy_course_by_non_admin_user(client):
    response = await client.delete('/courses/2')
    assert response.status_code == 403
    assert response.json()["detail"] == "You don't have enough permissions"
