
import pytest
import requests
import time

@pytest.fixture(scope="module")
def base_url():
    return "http://localhost:3000"

@pytest.fixture(scope="module")
def auth_token(base_url):
    credentials = {"username": "user123", "password": "password123"}
    response = requests.post(f"{base_url}/login", json=credentials)
    assert response.status_code == 200
    return response.json()["token"]

@pytest.fixture(scope="module")
def headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}

def test_login_success(base_url):
    credentials = {"username": "user123", "password": "password123"}
    response = requests.post(f"{base_url}/login", json=credentials)
    assert response.status_code == 200
    assert "token" in response.json()

def test_login_failure(base_url):
    credentials = {"username": "wrong", "password": "wrong"}
    response = requests.post(f"{base_url}/login", json=credentials)
    assert response.status_code == 401
    assert "detail" in response.json()
    assert response.json()["detail"] == "Invalid credentials"

def test_single_prediction(base_url, headers):
    input_data = {
        "gre_score": 309,
        "toefl_score": 108,
        "university_rating": 4,
        "sop": 3.0,
        "lor": 4.0,
        "cgpa": 7.94,
        "research": 0
    }
    response = requests.post(f"{base_url}/predict", headers=headers, json=input_data)
    assert response.status_code == 200
    prediction = response.json()
    assert "chance_of_admit" in prediction
    assert isinstance(prediction["chance_of_admit"], float)

def test_batch_prediction(base_url, headers):
    input_data = {
        "predictions": [
            {
                "gre_score": 309,
                "toefl_score": 108,
                "university_rating": 4,
                "sop": 3.0,
                "lor": 4.0,
                "cgpa": 7.94,
                "research": 0
            }
        ] * 3
    }
    
    response = requests.post(f"{base_url}/batch_predict", headers=headers, json=input_data)
    assert response.status_code == 200
    job_data = response.json()
    assert "job_id" in job_data
    assert job_data["status"] == "pending"
    
    job_id = job_data["job_id"]
    max_retries = 10
    retry_count = 0
    
    time.sleep(1)
    
    while retry_count < max_retries:
        status_response = requests.post(f"{base_url}/batch_status", headers=headers, json={"job_id": job_id})
        
        if status_response.status_code != 200:
            print(f"Statut de la réponse: {status_response.status_code}")
            print(f"Contenu de la réponse: {status_response.text}")
            time.sleep(1)
            retry_count += 1
            continue
        
        assert status_response.status_code == 200
        status_data = status_response.json()
        
        if status_data["status"] == "completed":
            break
            
        time.sleep(1)
        retry_count += 1
    
    assert status_data["status"] == "completed"
    assert "predictions" in status_data
    assert isinstance(status_data["predictions"], list)
    assert len(status_data["predictions"]) == 3
    
    for prediction in status_data["predictions"]:
        assert "chance_of_admit" in prediction
        assert isinstance(prediction["chance_of_admit"], float)