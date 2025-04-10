from testing_utils import *

logger = logging.getLogger("test.segb.api.history.get")

def test_GET_history():
    
    url = f"{BASE_URL}/log"
    headers = {
        "Content-Type": "text/turtle; charset=utf-8",
        "Authorization": f"Bearer {LOGGER_TOKEN}"
    }
    
    ttl_data_1 = """
        @prefix ex: <http://example.org/> .
        ex:subject1 ex:predicate "object1" .
    """
    
    ttl_data_2 = """
        @prefix ex: <http://example.org/> .
        ex:subject2 ex:predicate "object2" .
    """
    
    response1 = requests.post(url, headers=headers, data=ttl_data_1)
    assert response1.status_code == 201, f"Expected HTTP 201 Created code when inserting first TTL, but got {response1.status_code}"

    response2 = requests.post(url, headers=headers, data=ttl_data_2)
    assert response2.status_code == 201, f"Expected HTTP 201 Created code when inserting second TTL, but got {response2.status_code}"

    url = f"{BASE_URL}/history"
    headers = {
        "Authorization": f"Bearer {ADMIN_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    assert response.status_code == 200, f"Expected HTTP 200 OK code when getting history, but got {response.status_code}"
    
    history = response.json()
    assert len(history) == 2, f"Expected 2 history entries, but got {len(history)}"
    
    assert history[0]["action_type"] == "insertion", "First history entry action_type is incorrect"
    assert history[1]["action_type"] == "insertion", "Second history entry action_type is incorrect"
    
    assert "uploaded_at" in history[0], "First history entry is missing 'uploaded_at'"
    assert "uploaded_at" in history[1], "Second history entry is missing 'uploaded_at'"
    
    assert "origin_ip" in history[0], "First history entry is missing 'origin_ip'"
    assert "origin_ip" in history[1], "Second history entry is missing 'origin_ip'"

def test_GET_history_empty_graph():
    
    url = f"{BASE_URL}/history"
    headers = {
        "Authorization": f"Bearer {ADMIN_TOKEN}"
    }
    response = requests.get(url, headers=headers)

    assert response.status_code == 204, f"Expected HTTP 204 No Content when getting history, but got {response.status_code}"
    assert response.text.strip() == '', f"Expected empty response body for 204, but got: {response.text}"
