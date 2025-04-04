import pytest

import requests
import docker
import subprocess


BASE_URL = "http://127.0.0.1:5000"  
TEST_DB_VOLUME = "amor-segb-db-test"

def docker_compose_up():
    try:
        subprocess.run(['docker', 'compose', '-f', 'compose_tests.yaml', 'up', '-d'], check=True)
    except subprocess.CalledProcessError as e:
        pytest.fail(f'SEGB cannot be initiated: {e}')
        
def docker_compose_down():
    try:
        subprocess.run(['docker','compose', '-f', 'compose_tests.yaml', 'down'], check=True)
    except subprocess.CalledProcessError as e:
        pytest.fail(f'SEGB cannot be stopped: {e}')
        
import time
import requests

def wait_for_docker_service(url=BASE_URL, timeout=60, interval=2):
    start_time = time.time()
    while True:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return True
            else:
                pytest.fail(f'The SEGB failed when testing the connection. Expected 200 OK code, but got {response.status_code}')
        except requests.ConnectionError:
            continue

        if time.time() - start_time > timeout:
            pytest.fail(f'Timeout for the SEGB to initialize')

        time.sleep(interval)

        
        
def remove_database_docker_volume():
    client = docker.from_env()
    volumes = client.volumes.list()
    try:
        for vol in volumes:
            if TEST_DB_VOLUME in vol.name:
                vol.remove()
                break
    except docker.errors.NotFound:
        pass # if volume does not exist, the test just goes on
    except docker.errors.APIError as e:
        pytest.fail(f'Volume cannot be removed: {e}')



@pytest.fixture(autouse=True)
def setup_and_teardown():
    
    # SETUP
    remove_database_docker_volume()
    docker_compose_up()
    wait_for_docker_service()

    yield  

    #TEARDOWN
    docker_compose_down()
    

def test_GET_segb_is_working():
        
    response = requests.get(BASE_URL)
    assert response.status_code == 200, f"Expected HTTP 200 OK code, but got {response.status_code}"
    assert response.text == "The SEGB is working", f"Expected 'The SEGB is working', but got {response.text}"
    
        

def test_POST_log_valid_data():
    
    url = f"{BASE_URL}/log"
    headers = {"Content-Type": "text/turtle"}
    
    ttl_data = """
        @prefix ex: <http://example.org/> .
        ex:subject ex:predicate "object" .
    """
    response = requests.post(url, headers=headers, data=ttl_data)
    
    assert response.status_code == 200, f"Expected HTTP 200 0K code, but got {response.status_code}"
    
    
    
def test_POST_log_invalid_data():
    
        url = f"{BASE_URL}/log"
        headers = {"Content-Type": "text/turtle"}
        invalid_ttl_data = """
            prefix ex: http://example.org/> .
            ex:subject predicate "object" .
        """
        response = requests.post(url, headers=headers, data=invalid_ttl_data)
        
        assert response.status_code == 400, f"Expected 400 Bad Request, but got {response.status_code}"
        
        
def test_GET_empty_graph():
        
    url = f"{BASE_URL}/get_graph"
    response = requests.get(url)
    assert response.status_code == 204, f"Expected HTTP 204 Empty Content code, but got {response.status_code}"
    print(response.text, len(response.text))
    assert response.text == "", f"Expected empty response, but got {response.text}"


def test_GET_graph_with_one_POST():
    
    url = f"{BASE_URL}/log"
    headers = {"Content-Type": "text/turtle"}
    
    ttl_data = """
        @prefix ex: <http://example.org/> .
        ex:subject ex:predicate "object" .
    """
    response = requests.post(url, headers=headers, data=ttl_data)
    assert response.status_code == 200, f"Expected HTTP 200 OK code, but got {response.status_code}"
    
    url = f"{BASE_URL}/get_graph"
    response = requests.get(url)
    
    print(response.text)
    
    assert response.status_code == 200, f"Expected HTTP 200 OK code, but got {response.status_code}"
    assert "ex:subject ex:predicate \"object\" ." in response.text, "TTL data is missing in the response"
    assert "@prefix ex: <http://example.org/> ." in response.text, "@prefix is missing in the response"

    
def test_GET_graph_with_several_POST():

    url = f"{BASE_URL}/log"
    headers = {"Content-Type": "text/turtle"}
    
    ttl_data_1 = """
        @prefix ex: <http://example.org/> .
        ex:subject1 ex:predicate "object1" .
    """
    
    ttl_data_2 = """
        @prefix ex: <http://example.org/> .
        ex:subject2 ex:predicate "object2" .
    """

    response1 = requests.post(url, headers=headers, data=ttl_data_1)
    assert response1.status_code == 200, f"Expected HTTP 200 OK code, but got {response1.status_code}"
    
    response2 = requests.post(url, headers=headers, data=ttl_data_2)
    assert response2.status_code == 200, f"Expected HTTP 200 OK code, but got {response2.status_code}"

    url = f"{BASE_URL}/get_graph"
    response = requests.get(url)

    assert response.status_code == 200, f"Expected HTTP 200 OK code, but got {response.status_code}"
    response_text = response.text

    # Verify that the response includes ttl_data_1 and ttl_data_2
    assert "ex:subject1 ex:predicate \"object1\" ." in response_text, "ttl_data_1 is missing in the response"
    assert "ex:subject2 ex:predicate \"object2\" ." in response_text, "ttl_data_2 is missing in the response"

    # Verify that @prefix is not duplicated
    prefix_count = response_text.count("@prefix ex: <http://example.org/> .")
    assert prefix_count == 1, "@prefix is duplicated in the response" if prefix_count > 1 else "@prefix is missing in the response"
    
    
def test_GET_delete_graph():
    
    url = f"{BASE_URL}/log"
    headers = {"Content-Type": "text/turtle"}
    
    ttl_data = """
        @prefix ex: <http://example.org/> .
        ex:subject ex:predicate "object" .
    """
    response = requests.post(url, headers=headers, data=ttl_data)
    assert response.status_code == 200, f"Expected HTTP 200 OK code when inserting data, but got {response.status_code}"
    
    url = f"{BASE_URL}/clear_graph"
    response = requests.delete(url)
    print(response.text)
    
    assert response.status_code == 200, f"Expected HTTP 200 OK code when deleting graph, but got {response.status_code}"
    
    url = f"{BASE_URL}/get_graph"
    response = requests.get(url)
    
    assert response.status_code == 204, f"Expected HTTP 204 Empty Content code, but got {response.status_code}"
    assert response.text == "", f"Expected empty response, but got {response.text}"


    
def test_GET_history():
    
    url = f"{BASE_URL}/log"
    headers = {"Content-Type": "text/turtle"}
    
    ttl_data_1 = """
        @prefix ex: <http://example.org/> .
        ex:subject1 ex:predicate "object1" .
    """
    
    ttl_data_2 = """
        @prefix ex: <http://example.org/> .
        ex:subject2 ex:predicate "object2" .
    """
    
    response1 = requests.post(url, headers=headers, data=ttl_data_1)
    assert response1.status_code == 200, f"Expected HTTP 200 OK code when inserting first TTL, but got {response1.status_code}"

    response2 = requests.post(url, headers=headers, data=ttl_data_2)
    assert response2.status_code == 200, f"Expected HTTP 200 OK code when inserting second TTL, but got {response2.status_code}"

    url = f"{BASE_URL}/history"
    response = requests.get(url)
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
    response = requests.get(url)

    assert response.status_code == 204, f"Expected HTTP 204 No Content when getting history, but got {response.status_code}"
    assert response.text.strip() == '', f"Expected empty response body for 204, but got: {response.text}"
    
    
def test_GET_log():
    # Insert a log entry first
    url = f"{BASE_URL}/log"
    headers = {"Content-Type": "text/turtle"}
    
    ttl_data = """
        @prefix ex: <http://example.org/> .
        ex:subject ex:predicate "object" .
    """
    response = requests.post(url, headers=headers, data=ttl_data)
    assert response.status_code == 200, f"Expected HTTP 200 OK code when inserting log, but got {response.status_code}"
    
    # Retrieve the history to get the action_id
    url = f"{BASE_URL}/history"
    response = requests.get(url)
    assert response.status_code == 200, f"Expected HTTP 200 OK code when getting history, but got {response.status_code}"
    
    history = response.json()
    assert len(history) > 0, "Expected at least one history entry, but got none"

    log_id = history[0]["_id"]
    assert log_id, "Log ID is missing in the history entry"
    
    # Test the get_log endpoint
    url = f"{BASE_URL}/get_log?log_id={log_id}"
    response = requests.get(url)
    assert response.status_code == 200, f"Expected HTTP 200 OK code when getting log, but got {response.status_code}"
    
    log_data = response.json()
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
    
    
    
def test_GET_log_empty_graph():
    # Test the /get_log endpoint with no logs in the graph
    url = f"{BASE_URL}/get_log?log_id=nonexistent_id"
    response = requests.get(url)

    # Assert that the response status code is 404 (Log Info not found)
    assert response.status_code == 404, f"Expected HTTP 404 Not Found, but got {response.status_code}"
    assert response.json() == "Log Info not found", f"Expected 'Log Info not found', but got {response.json()}"

    # Test the /get_log endpoint without providing log_id
    url = f"{BASE_URL}/get_log"
    response = requests.get(url)

    # Assert that the response status code is 400 (Missing log_id parameter)
    assert response.status_code == 400, f"Expected HTTP 400 Bad Request, but got {response.status_code}"
    assert response.json() == "Missing log_id parameter", f"Expected 'Missing log_id parameter', but got {response.json()}"