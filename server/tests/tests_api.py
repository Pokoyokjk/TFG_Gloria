import pytest

import requests
import docker
import subprocess


BASE_URL = "http://127.0.0.1:5000"  


def docker_compose_up():
    try:
        subprocess.run(['docker', 'compose', 'up', '-d'], check=True)
    except subprocess.CalledProcessError as e:
        pytest.fail(f'SEGB cannot be initiated: {e}')
        
def docker_compose_down():
    try:
        subprocess.run(['docker','compose', 'down'], check=True)
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
    volume_name = 'sebb_amor-segb-db'
    try:
        volume = client.volumes.get(volume_name)
        volume.remove()
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
    
    