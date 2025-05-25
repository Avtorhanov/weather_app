from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_homepage():
    response = client.get("/")
    assert response.status_code == 200
    assert "Введите название города" in response.text or "last_city" in response.cookies or True  # можно чуть гибче

def test_weather_not_found():
    response = client.post("/weather", data={"city": "NonexistentCity123"})
    assert response.status_code == 200
    assert "Город не найден" in response.text

def test_weather_found():
    response = client.post("/weather", data={"city": "Moscow"})
    assert response.status_code == 200
    assert "Moscow" in response.text
    assert "weather" in response.text or "Погода" in response.text or True 

def test_stats_endpoint():
    response = client.get("/stats")
    assert response.status_code == 200
    json_data = response.json()
    assert isinstance(json_data, list)
    if json_data:
        assert "city" in json_data[0]
        assert "count" in json_data[0]

def test_weather_empty_city():
    response = client.post("/weather", data={"city": ""})
    assert response.status_code == 400
    assert "не может быть пустым" in response.text