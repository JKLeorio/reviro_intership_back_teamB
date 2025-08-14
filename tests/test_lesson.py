import py_compile

import pytest
from io import BytesIO
from api.auth import current_user
from datetime import datetime, timezone, timedelta


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
        'approximate_lesson_start':'12:00:00',
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

    lesson_response = await client.post(f'/lessons/group/{group_id}', json=lesson_data)
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

    response = await client.post(f"/lessons/group/{lesson_data['group_id']}", json=lesson_data)
    assert response.status_code == 201
    assert response.json()['teacher_id'] == lesson_data['teacher_id']


@pytest.mark.anyio
@pytest.mark.role('student')
async def test_create_lesson_by_student(client):
    lesson_data = {"name": "To be", "description": "How to use verb to be", "day": "2025-07-06",
                   "lesson_start": "09:00", "lesson_end": "11:15", "teacher_id": 1, "group_id": 1,
                   "classroom_id": 4}

    response = await client.post(f"/lessons/group/{lesson_data['group_id']}", json=lesson_data)
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

    response = await client.patch(f"/lessons/1", json={"teacher_id": teacher_id})

    assert response.status_code == 200
    assert response.json()['teacher_id'] == 1


@pytest.mark.anyio
@pytest.mark.role('teacher')
async def test_update_lesson(client):


    response = await client.patch(f"/lessons/1", json={"description": "Am, are, is"})


    assert response.status_code == 200
    assert response.json()['description'] == "Am, are, is"
    assert response.json()['link'] == "https://example.com/"


@pytest.mark.anyio
@pytest.mark.role('student')
async def test_update_lesson(client):

    response = await client.patch(f"/lessons/1", json={"name": "Am, are, is"})

    assert response.status_code == 403
    assert response.json()["detail"] == "You don't have enough permissions"


@pytest.mark.anyio
async def test_get_lessons(client):
    response = await client.get(f"/lessons/group/1/lessons")
    assert response.status_code == 200


@pytest.mark.anyio
@pytest.mark.role('student')
async def test_get_lessons(client, users, session):
    response = await client.get(f"/lessons/group/1/lessons")
    assert response.status_code == 403
    # assert isinstance(response.json(), list)


@pytest.mark.anyio
async def test_get_lesson(client):
    response = await client.get('/lessons/1')
    assert response.status_code == 200


@pytest.mark.anyio
async def test_create_homework_with_file_and_description(client):
    deadline = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()

    response = await client.post(
        f"/homeworks/lesson/1",
        data={"deadline": deadline, "description": "Read chapter 3"},
        files={"file": ("homework.txt", BytesIO(b"Some homework content"), "text/plain")},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["description"] == "Read chapter 3"
    assert "file_path" in data


@pytest.mark.anyio
async def test_update_homework(client):
    homework_id = 1

    new_description = "Updated homework description"
    new_deadline = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
    file_content = b"updated test file"
    file = BytesIO(file_content)
    file.name = "updated_homework.txt"

    response = await client.patch(
        f"/homeworks/{homework_id}",
        files={"file": ("updated_homework.txt", file, "text/plain")},
        data={
            "deadline": new_deadline,
            "description": new_description
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["description"] == new_description


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
async def test_submit_homework_with_no_file_and_no_content(client):
    homework_id = 1

    response = await client.post(f"/submissions/homework/{homework_id}", data={})

    assert response.status_code == 400
    assert response.json()["detail"] == "Either file or content must be provided"


@pytest.mark.anyio
async def test_get_homework_submission(client):
    homework_id = 1
    response = await client.get(f"/submissions/homework/{homework_id}")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.anyio
@pytest.mark.role("student")
async def test_get_homework_submission(client):
    response = await client.get(f"/submissions/homework/1")
    assert response.status_code == 403
    assert response.json()["detail"] == "You don't have enough permissions"


@pytest.mark.anyio
async def test_get_homework_submission(client):
    response = await client.get(f"/submissions/1")
    assert response.status_code == 200
    assert response.json()["content"] == "This is my homework text."


@pytest.mark.anyio
@pytest.mark.role("student")
async def test_get_homework_submission(client):
    response = await client.get(f"/submissions/1")
    # assert response.status_code == 200
    assert response.status_code == 403
    # assert response.json()["content"] == "This is my homework text."


@pytest.mark.anyio
@pytest.mark.role("student")
async def test_update_homework_submission(client):
    content_text = "This is my homework text content"

    response = await client.patch("/submissions/1", data={"content": content_text})

    # assert response.status_code == 200
    assert response.status_code == 403


@pytest.mark.anyio
async def test_create_homework_review(client):
    submission_id = 1
    data = {"comment": "Great job!"}

    response = await client.post(f"/homework_review/submission/{submission_id}", json=data)

    assert response.status_code == 201
    json_data = response.json()
    assert json_data["submission_id"] == submission_id
    assert json_data["comment"] == "Great job!"


@pytest.mark.anyio
@pytest.mark.role('student')
async def test_get_homework_review_by_id(client):
    response = await client.get("/homework_review/1")
    # assert response.status_code == 200
    assert response.status_code == 403
    # json_data = response.json()
    # assert "comment" in json_data


@pytest.mark.anyio
async def test_update_homework_review(client):
    data = {"comment": "Обновленный комментарий"}
    response = await client.patch("/homework_review/1", json=data)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["comment"] == data["comment"]


@pytest.mark.anyio
async def test_delete_homework_review(client):
    response = await client.delete("/homework_review/1")
    assert response.status_code == 200
    assert response.json()["detail"] == "Review with id 1 has been deleted"


@pytest.mark.anyio
@pytest.mark.role('student')
async def test_get_nonexistent_review(client):
    response = await client.get("/homework_review/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Review not found"


@pytest.mark.anyio
@pytest.mark.role('student')
async def test_forbidden_review_access(client):
    response = await client.get("/homework_review/2")
    if response.status_code == 403:
        assert response.json()["detail"] == "You are not allowed"


@pytest.mark.anyio
@pytest.mark.role('student')
async def test_destroy_homework_submission(client):

    response = await client.delete("/submissions/1")
    # assert response.status_code == 200
    assert response.status_code == 403
    # assert response.json()['detail'] == "Submission with id 1 has been deleted"


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
    response = await client.delete('/lessons/1')
    assert response.status_code == 200

