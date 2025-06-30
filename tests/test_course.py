import pytest


@pytest.mark.anyio
async def test_create_language(client):
    response = await client.post("/languages/", json={"name": "English"})
    assert response.status_code == 201
    assert response.json()["name"] == "English"


@pytest.mark.anyio
async def test_get_languages(client):
    response = await client.get("/languages/")
    assert response.status_code == 200
    return isinstance(response.json(), list)


@pytest.mark.anyio
async def test_get_language(client):
    create_resp = await client.post("/languages/", json={"name": "French"})
    assert create_resp.status_code == 201

    response = await client.get(f"/languages/2")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 2
    assert data["name"] == "French"


@pytest.mark.anyio
async def test_update_language(client):
    response = await client.patch("/languages/2", json={"name": "German"})
    assert response.status_code == 200
    assert response.json()["id"] == 2
    assert response.json()["name"] == "German"


@pytest.mark.anyio
async def test_destroy_language(client):
    response = await client.delete("/languages/2")
    assert response.status_code == 200
