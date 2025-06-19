import os
import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'AI' in response.data  # index.html 내 AI 텍스트 포함 여부

def test_ask_success(client, monkeypatch):
    # OpenAI API mocking
    def mock_generate_ai_response(message, persona, response_length):
        return "테스트 응답"
    import app.services
    monkeypatch.setattr(app.services, 'generate_ai_response', mock_generate_ai_response)
    data = {
        "message": "안녕?",
        "settings": {"persona": "professional", "responseLength": "short"}
    }
    response = client.post('/ask', json=data)
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] == 'success'
    assert json_data['response'] == "테스트 응답"

def test_ask_no_message(client):
    data = {"message": "", "settings": {}}
    response = client.post('/ask', json=data)
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['status'] == 'error'
    assert '메시지가 비어있습니다' in json_data['error']
