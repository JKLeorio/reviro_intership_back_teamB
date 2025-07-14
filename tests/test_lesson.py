import py_compile

import pytest
from io import BytesIO
from api.auth import current_user


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
async def test_create_lesson(client):
    new_user = {
        "email": "teacher@example.com",
        "first_name": "Test",
        "last_name": "Teacher",
        "role": "teacher",
    }

    response = await client.post("/auth/register-user", json=new_user)
    assert response.status_code == 201
    data = response.json()
    teacher_id = data['id']

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
    group_response = await client.post('/group/', json=group_data)
    assert group_response.status_code == 201
    assert group_response.json()['teacher']['id'] == teacher_id
    group_id = group_response.json()['id']

    classroom_response = await client.post("/classrooms/", json={"name": "Hamburg"})
    assert classroom_response.status_code == 201
    classroom_id = classroom_response.json()['id']

    lesson_data = {"name": "To be", "description": "How to use verb to be",
                   "link": "https://example.com/", "day": "2025-07-06",
                   "lesson_start": "09:00", "lesson_end": "11:15", "teacher_id": teacher_id, "group_id": group_id,
                   "classroom_id": classroom_id}

    lesson_response = await client.post(f'/lessons/group/{group_id}/new_lesson', json=lesson_data)
    assert lesson_response.status_code == 201
    assert lesson_response.json()["group_id"] == group_id
    assert lesson_response.json()["teacher_id"] == teacher_id
    assert lesson_response.json()["classroom_id"] == classroom_id


@pytest.mark.anyio
@pytest.mark.role('teacher')
async def test_create_lesson_by_teacher(client):
    lesson_data = {"name": "To be", "description": "How to use verb to be",
                   "link": "https://example.com/", "day": "2025-07-06",
                   "lesson_start": "09:00", "lesson_end": "11:15", "teacher_id": 1, "group_id": 1,
                   "classroom_id": 4}

    response = await client.post(f"/lessons/group/{lesson_data['group_id']}/new_lesson", json=lesson_data)
    assert response.status_code == 201
    assert response.json()['teacher_id'] == lesson_data['teacher_id']


@pytest.mark.anyio
@pytest.mark.role('student')
async def test_create_lesson_by_student(client):
    lesson_data = {"name": "To be", "description": "How to use verb to be", "day": "2025-07-06",
                   "lesson_start": "09:00", "lesson_end": "11:15", "teacher_id": 1, "group_id": 1,
                   "classroom_id": 4}

    response = await client.post(f"/lessons/group/{lesson_data['group_id']}/new_lesson", json=lesson_data)
    assert response.status_code == 403
    assert response.json()['detail'] == "You don't have enough permissions"


@pytest.mark.anyio
async def test_update_lesson(client):

    new_user = {
        "email": "teacher1@example.com",
        "first_name": "Test1",
        "last_name": "Teacher1",
        "role": "teacher",
    }

    user_response = await client.post("/auth/register-user", json=new_user)
    assert user_response.status_code == 201
    data = user_response.json()
    teacher_id = data['id']

    response = await client.patch(f"/lessons/lesson/1", json={"teacher_id": teacher_id})

    assert response.status_code == 200
    assert response.json()['teacher_id'] == 1


@pytest.mark.anyio
@pytest.mark.role('teacher')
async def test_update_lesson(client):

    response = await client.patch(f"/lessons/lesson/1", json={"description": "Am, are, is",
                                                              "link": "https://example.com/",})

    assert response.status_code == 200
    assert response.json()['description'] == "Am, are, is"
    assert response.json()['link'] == "https://example.com/"


@pytest.mark.anyio
@pytest.mark.role('student')
async def test_update_lesson(client):

    response = await client.patch(f"/lessons/lesson/1", json={"name": "Am, are, is"})

    assert response.status_code == 403
    assert response.json()["detail"] == "You don't have enough permissions"


@pytest.mark.anyio
async def test_get_lessons(client):
    response = await client.get(f"/lessons/group/1/lessons")
    assert response.status_code == 200


@pytest.mark.anyio
@pytest.mark.role('student')
async def test_get_lessons(client):
    response = await client.get(f"/lessons/group/1/lessons")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.anyio
async def test_get_lesson(client):
    response = await client.get('/lessons/lesson/1')
    assert response.status_code == 200


@pytest.mark.anyio
@pytest.mark.role('teacher')
async def test_create_homework(client):
    homework_data = {'deadline': '2025-08-08', "description": "write a simple sentences with new words"}
    response = await client.post('/homeworks/lesson/1/homework', json=homework_data)
    assert response.status_code == 201
    assert response.json()['lesson_id'] == 1
    assert response.json()['id'] == 1


@pytest.mark.anyio
@pytest.mark.role('student')
async def test_create_homework_by_student(client):
    homework_data = {'deadline': '2025-08-08', "description": "write simple sentences with new words"}
    response = await client.post('/homeworks/lesson/1/homework', json=homework_data)
    assert response.status_code == 403
    assert response.json()['detail'] == "You don't have enough permissions"


@pytest.mark.anyio
async def test_update_homework(client):
    updated_data = {"description": "write a simple sentences with new words and use new grammar"}
    response = await client.patch('/homeworks/1', json=updated_data)
    assert response.status_code == 200
    assert response.json()['id'] == 1
    assert response.json()['description'] == "write a simple sentences with new words and use new grammar"


@pytest.mark.anyio
@pytest.mark.role('student')
async def test_update_homework_by_student(client):
    updated_data = {"description": "write a simple sentences with new words and use new grammar"}
    response = await client.patch('/homeworks/1', json=updated_data)
    assert response.status_code == 403


@pytest.mark.anyio
async def test_submit_homework_with_file_and_content(client):
    homework_id = 1
    file_content = b"Test file content"
    file_name = "testfile.txt"
    content_text = "This is my homework text."

    files = {
        "file": (file_name, BytesIO(file_content), "text/plain"),
    }
    data = {
        "content": content_text
    }

    response = await client.post(f"/submissions/homework/{homework_id}", data=data, files=files)
    assert response.status_code == 201
    json_resp = response.json()
    assert json_resp["homework_id"] == homework_id
    assert json_resp["content"] == content_text
    assert json_resp["file_path"] is not None
    assert "submitted_at" in json_resp


@pytest.mark.anyio
async def test_submit_homework_with_content_only(client):
    homework_id = 1
    content_text = "This is my homework text content."

    data = {
        "content": content_text
    }

    response = await client.post(f"/submissions/homework/{homework_id}", data=data)

    assert response.status_code == 201
    json_resp = response.json()
    assert json_resp["homework_id"] == homework_id
    assert json_resp["content"] == content_text
    assert json_resp["file_path"] is None


@pytest.mark.anyio
async def test_submit_homework_with_no_file_and_no_content(client):
    homework_id = 1

    response = await client.post(f"/submissions/homework/{homework_id}", data={})

    assert response.status_code == 400
    assert response.json()["detail"] == "Either file or content must be provided"


@pytest.mark.anyio
async def test_get_homework_submission(client):
    response = await client.get(f"/submissions/homework/1")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.anyio
@pytest.mark.role("student")
async def test_get_homework_submission(client):
    response = await client.get(f"/submissions/homework/1")
    assert response.status_code == 403
    assert response.json()["detail"] == "You don't have enough permissions"


@pytest.mark.anyio
async def test_get_homework_submission(client):
    response = await client.get(f"/submissions/homework/1/submission/1")
    assert response.status_code == 200
    assert response.json()["content"] == "This is my homework text."


@pytest.mark.anyio
@pytest.mark.role("student")
async def test_get_homework_submission(client):
    response = await client.get(f"/submissions/homework/1/submission/2")
    assert response.status_code == 200
    assert response.json()["content"] == "This is my homework text content."


@pytest.mark.anyio
@pytest.mark.role("student")
async def test_update_homework_submission(client):
    content_text = "This is my homework text content"

    response = await client.patch("/submissions/homework/1/submission/2", data={"content": content_text})

    assert response.status_code == 200


@pytest.mark.anyio
@pytest.mark.role('student')
async def test_destroy_homework_submission(client):
    response = await client.delete("/submissions/homework/1/submission/2")
    assert response.status_code == 200
    assert response.json()['detail'] == "Submission with id 2 has been deleted from homework with id 1"


@pytest.mark.anyio
@pytest.mark.role('student')
async def test_destroy_homework_by_student(client):
    response = await client.delete('/homeworks/1')
    assert response.status_code == 403
    assert response.json()['detail'] == "You don't have enough permissions"


@pytest.mark.anyio
async def test_destroy_homework(client):
    response = await client.delete('/homeworks/1')
    assert response.status_code == 200
    assert response.json()['detail'] == "Homework with id 1 has been deleted"


@pytest.mark.anyio
async def test_destroy_lesson(client):
    response = await client.delete('/lessons/lesson/1')
    assert response.status_code == 200
