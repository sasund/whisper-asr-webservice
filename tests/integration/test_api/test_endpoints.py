from fastapi.testclient import TestClient

from app.webservice import app

client = TestClient(app)


def test_index_redirect():
    response = client.get("/")
    assert response.status_code in (200, 307, 302)
    assert "/docs" in response.text or response.headers.get("location") == "/docs"


def test_asr_endpoint_returns_422_on_no_file():
    response = client.post("/asr")
    assert response.status_code == 422


def test_detect_language_returns_422_on_no_file():
    response = client.post("/detect-language")
    assert response.status_code == 422
