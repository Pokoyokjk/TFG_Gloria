from testing_utils import *

logger = logging.getLogger("test.segb.api.log.get")

def test_GET_log():
    # Insert a log entry first
    url = f"{BASE_URL}/log"
    headers = {
        "Content-Type": "text/turtle; charset=utf-8",
        "Authorization": f"Bearer {ADMIN_TOKEN}"
    }
    
    ttl_data = """
        @prefix ex: <http://example.org/> .
        ex:subject ex:predicate "object" .
    """
    response = requests.post(url, headers=headers, data=ttl_data)
    assert response.status_code == 201, f"Expected HTTP 201 Created code when inserting log, but got {response.status_code}"
    
    # Retrieve the history to get the action_id
    url = f"{BASE_URL}/history"
    headers = {
        "Authorization": f"Bearer {ADMIN_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    assert response.status_code == 200, f"Expected HTTP 200 OK code when getting history, but got {response.status_code}"
    
    history = response.json()
    assert len(history) > 0, "Expected at least one history entry, but got none"

    log_id = history[0]["_id"]
    assert log_id, "Log ID is missing in the history entry"
    
    # Test the get log endpoint
    url = f"{BASE_URL}/log?log_id={log_id}"
    response = requests.get(url)
    headers = {
        "Authorization": f"Bearer {ADMIN_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    assert response.status_code == 200, f"Expected HTTP 200 OK code when getting log, but got {response.status_code}"
    
    log_data = response.json()
    logger.debug(f"Log data: {log_data}")
    assert "action" in log_data, "Response is missing 'action'"
    assert "ttl_content" in log_data["action"], "Action data is missing 'ttl_content'"
    assert log_data["action"]["ttl_content"].strip() == ttl_data.strip(), "TTL content does not match the inserted data"
    
    assert "log" in log_data, "Response is missing 'log'"
    assert "_id" in log_data["log"], "Log data is missing '_id'"
    assert log_data["log"]["_id"] == log_id, f"Expected log_id {log_id}, but got {log_data['log']['_id']}"
    assert "action_type" in log_data["log"], "Log data is missing 'action_type'"
    assert log_data["log"]["action_type"] == "insertion", f"Expected action_type 'insertion', but got {log_data['log']['action_type']}"
    assert "origin_ip" in log_data["log"], "Log data is missing 'origin_ip'"
    assert "uploaded_at" in log_data["log"], "Log data is missing 'uploaded_at'"
    
    expected_user_details: dict = jwt.decode(ADMIN_TOKEN, SECRET_KEY, algorithms=["HS256"])
    logger.debug(f"Decoded user details: {expected_user_details}")
    assert "user_details" in log_data["log"], "Log data is missing 'user_details'"
    assert expected_user_details.get("username") in log_data["log"]["user_details"], "username in user_details do not match"
    assert expected_user_details.get("name") in log_data["log"]["user_details"], "name in user_details do not match"
    for role in expected_user_details.get("roles"):
        assert role in log_data["log"]["user_details"], f"Role {role} in user_details do not match"
    assert str(expected_user_details.get("exp")) in log_data["log"]["user_details"], "expires in user_details do not match"

def test_GET_log_empty_graph():
    # Test the get /log endpoint with no logs in the graph
    url = f"{BASE_URL}/log?log_id=nonexistent_id"
    headers = {
        "Authorization": f"Bearer {ADMIN_TOKEN}"
    }
    response = requests.get(url, headers=headers)

    # Assert that the response status code is 404 (Log Info not found)
    assert response.status_code == 404, f"Expected HTTP 404 Not Found, but got {response.status_code}"

    # Test the get /log endpoint without providing log_id
    url = f"{BASE_URL}/log"
    headers = {
        "Authorization": f"Bearer {ADMIN_TOKEN}"
    }
    response = requests.get(url, headers=headers)

    # Assert that the response status code is 400 (Missing log_id parameter)
    assert response.status_code == 400, f"Expected HTTP 400 Bad Request, but got {response.status_code}"

def test_GET_log_with_json_params():
    '''
    Test the GET /log endpoint with JSON parameters.
    This test performs the following steps:
    1. Inserts a log entry using the POST /log endpoint with Turtle data.
    2. Retrieves the history using the GET /history endpoint to obtain the log ID.
    3. Attempts to retrieve the log using the GET /log endpoint with a JSON body containing the log ID.
    Assertions:
    - Ensures the POST /log request returns a 201 Created status code.
    - Ensures the GET /history request returns a 200 OK status code and contains at least one history entry.
    - Ensures the GET /log request with a JSON body returns a 400 Bad Request status code.
    Note:
    By convention, GET requests should not include a JSON body, as GET is intended to be idempotent and used for 
    retrieving resources based on query parameters or URL paths. While some servers may technically allow a JSON 
    body in GET requests, it is not standard practice and can lead to unexpected behavior or compatibility issues.
    '''
    # Insert a log entry first
    url = f"{BASE_URL}/log"
    headers = {
        "Content-Type": "text/turtle; charset=utf-8",
        "Authorization": f"Bearer {LOGGER_TOKEN}"
    }
    
    ttl_data = """
        @prefix ex: <http://example.org/> .
        ex:subject ex:predicate "object" .
    """
    response = requests.post(url, headers=headers, data=ttl_data)
    assert response.status_code == 201, f"Expected HTTP 201 Created code when inserting log, but got {response.status_code}"
    
    # Retrieve the history to get the action_id
    url = f"{BASE_URL}/history"
    headers = {
        "Authorization": f"Bearer {ADMIN_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    assert response.status_code == 200, f"Expected HTTP 200 OK code when getting history, but got {response.status_code}"
    
    history = response.json()
    assert len(history) > 0, "Expected at least one history entry, but got none"
    log_id = history[0]["_id"]
    assert log_id, "Log ID is missing in the history entry"
    
    # Test the get log endpoint with JSON parameters
    url = f"{BASE_URL}/log"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ADMIN_TOKEN}"
    }
    json_data = {"log_id": log_id}
    logger.debug(f"Log ID: {log_id}")
    response = requests.get(url, headers=headers, json=json_data)
    
    assert response.status_code == 400, f"Expected HTTP 400 Bad Request code, but got {response.status_code}"
