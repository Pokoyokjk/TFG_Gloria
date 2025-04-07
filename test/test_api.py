import pytest

from rdflib import Graph
import requests
import docker
import subprocess
import logging
import os

# Set up logging
from dotenv import load_dotenv
# Load environment variables from a .env file
load_dotenv("./test/test.env")

logging_level = os.getenv("LOGGING_LEVEL", "INFO").upper()
log_file = os.getenv("TESTS_LOG_FILE", "test_segb_server.log")
compose_file = os.getenv("COMPOSE_FILE", "./test/docker-compose.test.yaml")
# Ensure the logs directory exists
os.makedirs('./test/logs', exist_ok=True)
file_handler = logging.FileHandler(
    filename=f'./test/logs/{log_file}',
    mode='a',
    encoding='utf-8'
)
file_handler.setFormatter(logging.Formatter(
    fmt='%(asctime)s - %(name)s - %(levelname)s -> %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
))
logger = logging.getLogger("SEGB Test Logger")
logger.setLevel(getattr(logging, logging_level, logging.INFO))
logger.addHandler(file_handler)


logger.info("Starting tests for the SEGB server...")
logger.info("Logging level set to %s", logging_level)

logger.debug(f"For paths, checking working directory: {os.getcwd()}")
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:5000")
TEST_DB_VOLUME = os.getenv("TEST_DB_VOLUME", "amor-segb-db-test")

logger.info(f"Loading test tokens from environment variables")
READER_TOKEN = os.getenv("READER_TOKEN", "fake_reader_token")
LOGGER_TOKEN = os.getenv("LOGGER_TOKEN", "fake_logger_token")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "fake_admin_token")

SECRET_KEY = os.getenv("SECRET_KEY", None)

if SECRET_KEY:
    logger.info("The Testing SEGB server is SECURED with a secret key.")
else:
    logger.info("The Testing SEGB server is NOT SECURED with a secret key.")

def docker_compose_up():
    try:
        logger.debug(f'Running docker compose up with file: {compose_file}')
        subprocess.run(['docker', 'compose', '-f', compose_file, 'up', '-d'], check=True)
    except subprocess.CalledProcessError as e:
        pytest.fail(f'SEGB cannot be initiated: {e}')
        
def docker_compose_down():
    try:
        logger.debug(f'Running docker compose down with file: {compose_file}')
        subprocess.run(['docker', 'compose', '-f', compose_file, 'down'], check=True)
    except subprocess.CalledProcessError as e:
        pytest.fail(f'SEGB cannot be stopped: {e}')
        
import time
import requests

def wait_for_docker_service(url=f'{BASE_URL}/health', timeout=60, interval=2):
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
                logger.debug(f"Removed volume: {vol.name}")
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
    

def test_GET_healthcheck():
    
    response = requests.get(BASE_URL + "/health")
    assert response.status_code == 200, f"Expected HTTP 200 OK code, but got {response.status_code}"
    assert response.text == "The SEGB is working", f"Expected 'The SEGB is working', but got {response.text}"
    

def test_POST_log_valid_data_with_admin_token():
    url = f"{BASE_URL}/log"
    headers = {
        "Content-Type": "text/turtle",
        "Authorization": f"Bearer {ADMIN_TOKEN}"
    }
    
    ttl_data = """
        @prefix ex: <http://example.org/> .
        ex:subject ex:predicate "object" .
    """
    response = requests.post(url, headers=headers, data=ttl_data)
    
    assert response.status_code == 201, f"Expected HTTP 201 Created code, but got {response.status_code}"

def test_POST_log_valid_data_with_logger_token():
    url = f"{BASE_URL}/log"
    headers = {
        "Content-Type": "text/turtle",
        "Authorization": f"Bearer {LOGGER_TOKEN}"
    }
    
    ttl_data = """
        @prefix ex: <http://example.org/> .
        ex:subject ex:predicate "object" .
    """
    response = requests.post(url, headers=headers, data=ttl_data)
    
    assert response.status_code == 201, f"Expected HTTP 201 Created code, but got {response.status_code}"

def test_POST_log_valid_data_with_reader_token():
    url = f"{BASE_URL}/log"
    headers = {
        "Content-Type": "text/turtle",
        "Authorization": f"Bearer {READER_TOKEN}"
    }
    
    ttl_data = """
        @prefix ex: <http://example.org/> .
        ex:subject ex:predicate "object" .
    """
    response = requests.post(url, headers=headers, data=ttl_data)
    if SECRET_KEY:
        assert response.status_code == 403, f"Expected HTTP 403 Forbidden code, but got {response.status_code}"
    else:
        assert response.status_code == 201, f"Expected HTTP 201 Created code, but got {response.status_code}"

def test_POST_log_invalid_data():
    url = f"{BASE_URL}/log"
    headers = {
        "Content-Type": "text/turtle",
        "Authorization": f"Bearer {LOGGER_TOKEN}"
    }
    invalid_ttl_data = """
        prefix ex: http://example.org/> .
        ex:subject predicate "object" .
    """
    response = requests.post(url, headers=headers, data=invalid_ttl_data)
    
    assert response.status_code == 400, f"Expected 400 Bad Request, but got {response.status_code}"

def test_GET_empty_graph():
    url = f"{BASE_URL}/graph"
    headers = {
        "Authorization": f"Bearer {READER_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    assert response.status_code == 204, f"Expected HTTP 204 Empty Content code, but got {response.status_code}"
    logger.debug(f"Response text: {response.text}")
    logger.debug(f"Response length: {len(response.text)}")
    assert response.text == "", f"Expected empty response, but got {response.text}"

def test_GET_graph_with_one_POST():
    
    url = f"{BASE_URL}/log"
    headers = {
        "Content-Type": "text/turtle",
        "Authorization": f"Bearer {LOGGER_TOKEN}"
    }
    
    ttl_data = """
        @prefix ex: <http://example.org/> .
        ex:subject ex:predicate "object" .
    """
    response = requests.post(url, headers=headers, data=ttl_data)
    assert response.status_code == 201, f"Expected HTTP 201 Created code, but got {response.status_code}"
    
    time.sleep(3)  # Wait for the data to be processed and available in the graph
    
    url = f"{BASE_URL}/graph"
    headers = {
        "Authorization": f"Bearer {READER_TOKEN}"
    }
    response = requests.get(url, headers=headers, stream=True)
    logger.debug(f"Response text: {response.text}")
    assert response.status_code == 200, f"Expected HTTP 200 OK code, but got {response.status_code}"
    assert "ex:subject ex:predicate \"object\" ." in response.text, "TTL data is missing in the response"
    assert "@prefix ex: <http://example.org/> ." in response.text, "@prefix is missing in the response"

def test_GET_graph_with_several_POST():

    url = f"{BASE_URL}/log"
    headers = {
        "Content-Type": "text/turtle",
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
    assert response1.status_code == 201, f"Expected HTTP 201 Created code, but got {response1.status_code}"
    
    response2 = requests.post(url, headers=headers, data=ttl_data_2)
    assert response2.status_code == 201, f"Expected HTTP 201 Created code, but got {response2.status_code}"

    url = f"{BASE_URL}/graph"
    headers = {
        "Authorization": f"Bearer {READER_TOKEN}"
    }
    response = requests.get(url, headers=headers, stream=True)
    logger.debug(f"Response length: {len(response.text)}")
    assert response.status_code == 200, f"Expected HTTP 200 OK code, but got {response.status_code}"
    response_text = response.text
    # Verify that the response includes ttl_data_1 and ttl_data_2
    assert "ex:subject1 ex:predicate \"object1\" ." in response_text, "ttl_data_1 is missing in the response"
    assert "ex:subject2 ex:predicate \"object2\" ." in response_text, "ttl_data_2 is missing in the response"
    # Verify that @prefix is not duplicated
    prefix_count = response_text.count("@prefix ex: <http://example.org/> .")
    assert prefix_count == 1, "@prefix is duplicated in the response" if prefix_count > 1 else "@prefix is missing in the response"

def test_DELETE_graph():
    
    url = f"{BASE_URL}/log"
    headers = {
        "Content-Type": "text/turtle",
        "Authorization": f"Bearer {ADMIN_TOKEN}"
    }
    
    ttl_data = """
        @prefix ex: <http://example.org/> .
        ex:subject ex:predicate "object" .
    """
    response = requests.post(url, headers=headers, data=ttl_data)
    assert response.status_code == 201, f"Expected HTTP 201 Created code, but got {response.status_code}"
    
    url = f"{BASE_URL}/graph"
    headers = {
        "Authorization": f"Bearer {ADMIN_TOKEN}"
    }
    response = requests.delete(url, headers=headers)
    print(response.text)
    
    assert response.status_code == 200, f"Expected HTTP 200 OK code when deleting graph, but got {response.status_code}"
    
    response = requests.get(url, headers=headers)
    
    assert response.status_code == 204, f"Expected HTTP 204 Empty Content code, but got {response.status_code}"
    assert response.text == "", f"Expected empty response, but got {response.text}"

def test_DELETE_empty_graph():
    # Test the DELETE /graph endpoint when the graph is already empty
    
    # Ensure the graph is empty by attempting to delete it first
    url = f"{BASE_URL}/graph"
    headers = {
        "Authorization": f"Bearer {ADMIN_TOKEN}"
    }
    response = requests.delete(url, headers=headers)
    assert response.status_code in [200, 204], f"Expected HTTP 200 or 204 when ensuring graph is empty, but got {response.status_code}"
    
    # Attempt to delete the graph again
    response = requests.delete(url, headers=headers)
    assert response.status_code == 204, f"Expected HTTP 204 No Content when deleting an already empty graph, but got {response.status_code}"
    assert response.text.strip() == "", f"Expected empty response body for 204, but got: {response.text}"

def test_GET_history():
    
    url = f"{BASE_URL}/log"
    headers = {
        "Content-Type": "text/turtle",
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

def test_GET_log():
    # Insert a log entry first
    url = f"{BASE_URL}/log"
    headers = {
        "Content-Type": "text/turtle",
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

def test_GET_experiments_basic():
    # Test the /experiments endpoint
    
    # Insert a log entry to populate the SEGB
    url = f"{BASE_URL}/log"
    headers = {
        "Content-Type": "text/turtle",
        "Authorization": f"Bearer {LOGGER_TOKEN}"
    }
    
    # Example TTL data for experiments
    ttl_data = """
        @prefix amor-exp: <http://www.gsi.upm.es/ontologies/amor/experiments/ns#> .
        @prefix amor-exec: <http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#> .
        
        amor-exec:exp1 a amor-exp:Experiment .
        amor-exec:exp2 a amor-exp:Experiment .
        amor-exec:exp3 a amor-exp:Experiment .
        amor-exec:exp4 a amor-exp:Experiment .
    """
    response = requests.post(url, headers=headers, data=ttl_data)
    assert response.status_code == 201, f"Expected HTTP 201 Created code when inserting log, but got {response.status_code}"
    
    url = f"{BASE_URL}/experiments"
    headers = {
        "Authorization": f"Bearer {READER_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    assert response.status_code == 200, f"Expected HTTP 200 OK code, but got {response.status_code}"
    
    # Parse the response JSON and verify the experiment URIs
    resulting_uris = response.json()
    expected_uris = [
        "http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#exp1",
        "http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#exp2",
        "http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#exp3",
        "http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#exp4",
    ]

    # Verify that both have the same length
    logger.debug(f"Experiment list: {resulting_uris}")
    logger.debug(f"Expected URIs: {expected_uris}")
    
    # Verify that all expected URIs are present in the response
    assert len(resulting_uris) == len(expected_uris), f"Expected {len(expected_uris)} URIs, but got {len(resulting_uris)}"
    for uri in expected_uris:
        assert uri in resulting_uris, f"Expected URI {uri} is missing in the response"

    # Verify that there are no unexpected URIs in the response
    for uri in resulting_uris:
        assert uri in expected_uris, f"Unexpected URI {uri} found in the response"

def test_GET_experiments_extended():
    # Test the /experiments endpoint
    
    # Insert a log entry to populate the SEGB
    url = f"{BASE_URL}/log"
    headers = {
        "Content-Type": "text/turtle",
        "Authorization": f"Bearer {LOGGER_TOKEN}"
    }
    
    # Example TTL data for experiments
    ttl_data = """
        @prefix amor-exp: <http://www.gsi.upm.es/ontologies/amor/experiments/ns#> .
        @prefix amor-exec: <http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#> .
        
        amor-exec:exp1 a amor-exp:Experiment ;
            amor-exp:hasExecutor amor-exec:ari41 ;
            amor-exp:hasRequester amor-exec:researcher1 ;
            amor-exp:hasExperimentationSubject amor-exec:user_moralbias_001 .
        amor-exec:exp2 a amor-exp:Experiment ;
            amor-exp:hasExecutor amor-exec:ari42 ;
            amor-exp:hasRequester amor-exec:researcher2 ;
            amor-exp:hasExperimentationSubject amor-exec:user_moralbias_002 .
        amor-exec:exp3 a amor-exp:Experiment ;
            amor-exp:hasExecutor amor-exec:ari43 ;
            amor-exp:hasExperimentationSubject amor-exec:user_moralbias_002 .
        amor-exec:exp4 a amor-exp:Experiment ;
            amor-exp:hasRequester amor-exec:researcher2 ;
            amor-exp:hasExperimentationSubject amor-exec:user_moralbias_002 .
    """
    response = requests.post(url, headers=headers, data=ttl_data)
    assert response.status_code == 201, f"Expected HTTP 201 Created code when inserting log, but got {response.status_code}"
    
    url = f"{BASE_URL}/experiments"
    headers = {
        "Authorization": f"Bearer {READER_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    assert response.status_code == 200, f"Expected HTTP 200 OK code, but got {response.status_code}"
    
    # Parse the response JSON and verify the experiment URIs
    resulting_uris = response.json()
    expected_uris = [
        "http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#exp1",
        "http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#exp2",
        "http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#exp3",
        "http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#exp4",
    ]

    # Verify that both have the same length
    logger.debug(f"Experiment list: {resulting_uris}")
    logger.debug(f"Expected URIs: {expected_uris}")
    assert len(resulting_uris) == len(expected_uris), f"Expected {len(expected_uris)} URIs, but got {len(resulting_uris)}"
    
    # Verify that all expected URIs are present in the response
    for uri in expected_uris:
        assert uri in resulting_uris, f"Expected URI {uri} is missing in the response"

    # Verify that there are no unexpected URIs in the response
    for uri in resulting_uris:
        assert uri in expected_uris, f"Unexpected URI {uri} found in the response"

def test_GET_experiments_extended_several_logs():
    # Test the /experiments endpoint
    
    # Insert a log entry to populate the SEGB
    url = f"{BASE_URL}/log"
    headers = {
        "Content-Type": "text/turtle",
        "Authorization": f"Bearer {LOGGER_TOKEN}"
    }
    
    # Example TTL data for experiments
    ttl_data = """
        @prefix amor-exp: <http://www.gsi.upm.es/ontologies/amor/experiments/ns#> .
        @prefix amor-exec: <http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#> .
        
        amor-exec:exp1 a amor-exp:Experiment ;
            amor-exp:hasExecutor amor-exec:ari41 ;
            amor-exp:hasRequester amor-exec:researcher1 ;
            amor-exp:hasExperimentationSubject amor-exec:user_moralbias_001 .
        amor-exec:exp2 a amor-exp:Experiment ;
            amor-exp:hasExecutor amor-exec:ari42 ;
            amor-exp:hasRequester amor-exec:researcher2 ;
            amor-exp:hasExperimentationSubject amor-exec:user_moralbias_002 .
        amor-exec:exp3 a amor-exp:Experiment ;
            amor-exp:hasExecutor amor-exec:ari43 ;
            amor-exp:hasExperimentationSubject amor-exec:user_moralbias_002 .
        amor-exec:exp4 a amor-exp:Experiment ;
            amor-exp:hasRequester amor-exec:researcher2 ;
            amor-exp:hasExperimentationSubject amor-exec:user_moralbias_002 .
    """
    response = requests.post(url, headers=headers, data=ttl_data)
    assert response.status_code == 201, f"Expected HTTP 201 Created code when inserting log, but got {response.status_code}"
    
    ttl_data = """
        @prefix amor-exp: <http://www.gsi.upm.es/ontologies/amor/experiments/ns#> .
        @prefix amor-exec: <http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#> .
        
        amor-exec:exp1 a amor-exp:Experiment .
        amor-exec:exp5 a amor-exp:Experiment .
        amor-exec:exp3 a amor-exp:Experiment .
        amor-exec:exp6 a amor-exp:Experiment .
    """
    response = requests.post(url, headers=headers, data=ttl_data)
    assert response.status_code == 201, f"Expected HTTP 201 Created code when inserting log, but got {response.status_code}"
    
    url = f"{BASE_URL}/experiments"
    headers = {
        "Authorization": f"Bearer {READER_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    assert response.status_code == 200, f"Expected HTTP 200 OK code, but got {response.status_code}"
    
    # Parse the response JSON and verify the experiment URIs
    resulting_uris = response.json()
    expected_uris = [
        "http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#exp1",
        "http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#exp2",
        "http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#exp3",
        "http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#exp4",
        "http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#exp5",
        "http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#exp6",
    ]

    # Verify that both have the same length
    logger.debug(f"Experiment list: {resulting_uris}")
    logger.debug(f"Expected URIs: {expected_uris}")
    assert len(resulting_uris) == len(expected_uris), f"Expected {len(expected_uris)} URIs, but got {len(resulting_uris)}"

    # Verify that all expected URIs are present in the response
    for uri in expected_uris:
        assert uri in resulting_uris, f"Expected URI {uri} is missing in the response"

    # Verify that there are no unexpected URIs in the response
    for uri in resulting_uris:
        assert uri in expected_uris, f"Unexpected URI {uri} found in the response"

def test_GET_experiments_without_logged_experiments():
    # Test the /experiments endpoint
    
    url = f"{BASE_URL}/experiments"
    headers = {
        "Authorization": f"Bearer {READER_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    assert response.status_code == 204, f"Expected HTTP 204 No Content code, but got {response.status_code}"

def test_GET_experiment():
    # Test the /experiments endpoint
    
    # Insert a log entry to populate the SEGB
    url = f"{BASE_URL}/log"
    headers = {
        "Content-Type": "text/turtle",
        "Authorization": f"Bearer {LOGGER_TOKEN}"
    }
    
    # Example TTL data for experiments
    ttl_data = """
        @prefix amor-exp: <http://www.gsi.upm.es/ontologies/amor/experiments/ns#> .
        @prefix amor-exec: <http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#> .
        
        amor-exec:exp1 a amor-exp:Experiment ;
            amor-exp:hasExecutor amor-exec:ari41 ;
            amor-exp:hasRequester amor-exec:researcher1 ;
            amor-exp:hasExperimentationSubject amor-exec:user_moralbias_001 .
        amor-exec:exp2 a amor-exp:Experiment ;
            amor-exp:hasExecutor amor-exec:ari42 ;
            amor-exp:hasRequester amor-exec:researcher2 ;
            amor-exp:hasExperimentationSubject amor-exec:user_moralbias_002 .
        amor-exec:exp3 a amor-exp:Experiment ;
            amor-exp:hasExecutor amor-exec:ari43 ;
            amor-exp:hasExperimentationSubject amor-exec:user_moralbias_002 .
        amor-exec:exp4 a amor-exp:Experiment ;
            amor-exp:hasRequester amor-exec:researcher2 ;
            amor-exp:hasExperimentationSubject amor-exec:user_moralbias_002 .
    """
    response = requests.post(url, headers=headers, data=ttl_data)
    assert response.status_code == 201, f"Expected HTTP 201 Created code when inserting log, but got {response.status_code}"
    
    # Test the get /experiments endpoint    
    url = f"{BASE_URL}/experiments?namespace=http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns&experiment_id=exp1"
    headers = {
        "Authorization": f"Bearer {READER_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    
    assert response.status_code == 200, f"Expected HTTP 200 OK code, but got {response.status_code}"
    
    # Load the response into an RDFLib graph
    graph = Graph()
    graph.parse(data=response.text, format="turtle")


    # Log all triples in the graph
    for subj, pred, obj in graph:
        logger.debug(f"Triple found:\n{subj} {pred} {obj}")
    # Verify that the graph is not empty
    assert len(graph) > 0, "The RDF graph is empty"
    # Verify that the expected triples are present in the graph
    expected_graph = Graph()
    expected_ttl_data = """
        @prefix amor-exp: <http://www.gsi.upm.es/ontologies/amor/experiments/ns#> .
        @prefix amor-exec: <http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#> .
        
        amor-exec:exp1 a amor-exp:Experiment ;
            amor-exp:hasExecutor amor-exec:ari41 ;
            amor-exp:hasRequester amor-exec:researcher1 ;
            amor-exp:hasExperimentationSubject amor-exec:user_moralbias_001 .
    """
    expected_graph.parse(data=expected_ttl_data, format="turtle")

    # Compare the two graphs
    assert len(graph) == len(expected_graph), f"Graph lengths differ: expected {len(expected_graph)}, got {len(graph)}"

    for triple in expected_graph:
        assert triple in graph, f"Expected triple {triple} is missing in the graph"

    for triple in graph:
        assert triple in expected_graph, f"Unexpected triple {triple} found in the graph"

def test_GET_experiment_query_hastag_code():
    # Test the /experiments endpoint
    
    # Insert a log entry to populate the SEGB
    url = f"{BASE_URL}/log"
    headers = {
        "Content-Type": "text/turtle",
        "Authorization": f"Bearer {LOGGER_TOKEN}"
    }
    
    # Example TTL data for experiments
    ttl_data = """
        @prefix amor-exp: <http://www.gsi.upm.es/ontologies/amor/experiments/ns#> .
        @prefix amor-exec: <http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#> .
        
        amor-exec:exp1 a amor-exp:Experiment ;
            amor-exp:hasExecutor amor-exec:ari41 ;
            amor-exp:hasRequester amor-exec:researcher1 ;
            amor-exp:hasExperimentationSubject amor-exec:user_moralbias_001 .
        amor-exec:exp2 a amor-exp:Experiment ;
            amor-exp:hasExecutor amor-exec:ari42 ;
            amor-exp:hasRequester amor-exec:researcher2 ;
            amor-exp:hasExperimentationSubject amor-exec:user_moralbias_002 .
        amor-exec:exp3 a amor-exp:Experiment ;
            amor-exp:hasExecutor amor-exec:ari43 ;
            amor-exp:hasExperimentationSubject amor-exec:user_moralbias_002 .
        amor-exec:exp4 a amor-exp:Experiment ;
            amor-exp:hasRequester amor-exec:researcher2 ;
            amor-exp:hasExperimentationSubject amor-exec:user_moralbias_002 .
    """
    response = requests.post(url, headers=headers, data=ttl_data)
    assert response.status_code == 201, f"Expected HTTP 201 Created code when inserting log, but got {response.status_code}"
    
    # Test the get /experiments endpoint    
    url = f"{BASE_URL}/experiments?namespace=http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns%23&experiment_id=exp3"
    headers = {
        "Authorization": f"Bearer {READER_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    
    assert response.status_code == 200, f"Expected HTTP 200 OK code, but got {response.status_code}"
    
    # Load the response into an RDFLib graph
    graph = Graph()
    graph.parse(data=response.text, format="turtle")


    # Log all triples in the graph
    for subj, pred, obj in graph:
        logger.debug(f"Triple found:\n{subj} {pred} {obj}")
    # Verify that the graph is not empty
    assert len(graph) > 0, "The RDF graph is empty"
    # Verify that the expected triples are present in the graph
    expected_graph = Graph()
    expected_ttl_data = """
        @prefix amor-exp: <http://www.gsi.upm.es/ontologies/amor/experiments/ns#> .
        @prefix amor-exec: <http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#> .
        
        amor-exec:exp3 a amor-exp:Experiment ;
            amor-exp:hasExecutor amor-exec:ari43 ;
            amor-exp:hasExperimentationSubject amor-exec:user_moralbias_002 .
    """
    expected_graph.parse(data=expected_ttl_data, format="turtle")

    # Compare the two graphs
    assert len(graph) == len(expected_graph), f"Graph lengths differ: expected {len(expected_graph)}, got {len(graph)}"

    for triple in expected_graph:
        assert triple in graph, f"Expected triple {triple} is missing in the graph"

    for triple in graph:
        assert triple in expected_graph, f"Unexpected triple {triple} found in the graph"

def test_GET_experiment_query_params():
    # Test the /experiments endpoint
    
    # Insert a log entry to populate the SEGB
    url = f"{BASE_URL}/log"
    headers = {
        "Content-Type": "text/turtle",
        "Authorization": f"Bearer {LOGGER_TOKEN}"
    }
    
    # Example TTL data for experiments
    ttl_data = """
        @prefix amor-exp: <http://www.gsi.upm.es/ontologies/amor/experiments/ns#> .
        @prefix amor-exec: <http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#> .
        
        amor-exec:exp1 a amor-exp:Experiment ;
            amor-exp:hasExecutor amor-exec:ari41 ;
            amor-exp:hasRequester amor-exec:researcher1 ;
            amor-exp:hasExperimentationSubject amor-exec:user_moralbias_001 .
        amor-exec:exp2 a amor-exp:Experiment ;
            amor-exp:hasExecutor amor-exec:ari42 ;
            amor-exp:hasRequester amor-exec:researcher2 ;
            amor-exp:hasExperimentationSubject amor-exec:user_moralbias_002 .
        amor-exec:exp3 a amor-exp:Experiment ;
            amor-exp:hasExecutor amor-exec:ari43 ;
            amor-exp:hasExperimentationSubject amor-exec:user_moralbias_002 .
        amor-exec:exp4 a amor-exp:Experiment ;
            amor-exp:hasRequester amor-exec:researcher2 ;
            amor-exp:hasExperimentationSubject amor-exec:user_moralbias_002 .
    """
    response = requests.post(url, headers=headers, data=ttl_data)
    assert response.status_code == 201, f"Expected HTTP 201 Created code when inserting log, but got {response.status_code}"
    
    # Test the get /experiments endpoint    
    url = f"{BASE_URL}/experiments"
    headers = {
        "Authorization": f"Bearer {READER_TOKEN}"
    }
    params = {
        "experiment_id": "exp3",
        "namespace": "http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#"
    }
    response = requests.get(url, headers=headers, params=params)
    
    assert response.status_code == 200, f"Expected HTTP 200 OK code, but got {response.status_code}"
    
    # Load the response into an RDFLib graph
    graph = Graph()
    graph.parse(data=response.text, format="turtle")


    # Log all triples in the graph
    for subj, pred, obj in graph:
        logger.debug(f"Triple found:\n{subj} {pred} {obj}")
    # Verify that the graph is not empty
    assert len(graph) > 0, "The RDF graph is empty"
    # Verify that the expected triples are present in the graph
    expected_graph = Graph()
    expected_ttl_data = """
        @prefix amor-exp: <http://www.gsi.upm.es/ontologies/amor/experiments/ns#> .
        @prefix amor-exec: <http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#> .
        
        amor-exec:exp3 a amor-exp:Experiment ;
            amor-exp:hasExecutor amor-exec:ari43 ;
            amor-exp:hasExperimentationSubject amor-exec:user_moralbias_002 .
    """
    expected_graph.parse(data=expected_ttl_data, format="turtle")

    # Compare the two graphs
    assert len(graph) == len(expected_graph), f"Graph lengths differ: expected {len(expected_graph)}, got {len(graph)}"

    for triple in expected_graph:
        assert triple in graph, f"Expected triple {triple} is missing in the graph"

    for triple in graph:
        assert triple in expected_graph, f"Unexpected triple {triple} found in the graph"

def test_GET_experiment_uri():
    # Test the /experiments endpoint
    
    # Insert a log entry to populate the SEGB
    url = f"{BASE_URL}/log"
    headers = {
        "Content-Type": "text/turtle",
        "Authorization": f"Bearer {LOGGER_TOKEN}"
    }
    
    # Example TTL data for experiments
    ttl_data = """
        @prefix amor-exp: <http://www.gsi.upm.es/ontologies/amor/experiments/ns#> .
        @prefix amor-exec: <http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#> .
        
        amor-exec:exp1 a amor-exp:Experiment ;
            amor-exp:hasExecutor amor-exec:ari41 ;
            amor-exp:hasRequester amor-exec:researcher1 ;
            amor-exp:hasExperimentationSubject amor-exec:user_moralbias_001 .
        amor-exec:exp2 a amor-exp:Experiment ;
            amor-exp:hasExecutor amor-exec:ari42 ;
            amor-exp:hasRequester amor-exec:researcher2 ;
            amor-exp:hasExperimentationSubject amor-exec:user_moralbias_002 .
        amor-exec:exp3 a amor-exp:Experiment ;
            amor-exp:hasExecutor amor-exec:ari43 ;
            amor-exp:hasExperimentationSubject amor-exec:user_moralbias_002 .
        amor-exec:exp4 a amor-exp:Experiment ;
            amor-exp:hasRequester amor-exec:researcher2 ;
            amor-exp:hasExperimentationSubject amor-exec:user_moralbias_002 .
    """
    response = requests.post(url, headers=headers, data=ttl_data)
    assert response.status_code == 201, f"Expected HTTP 201 Created code when inserting log, but got {response.status_code}"
    
    # Test the get /experiments endpoint    
    url = f"{BASE_URL}/experiments?uri=http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns%23exp1"
    headers = {
        "Authorization": f"Bearer {READER_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    
    assert response.status_code == 200, f"Expected HTTP 200 OK code, but got {response.status_code}"
    
    # Load the response into an RDFLib graph
    graph = Graph()
    graph.parse(data=response.text, format="turtle")


    # Log all triples in the graph
    for subj, pred, obj in graph:
        logger.debug(f"Triple found:\n{subj} {pred} {obj}")
    # Verify that the graph is not empty
    assert len(graph) > 0, "The RDF graph is empty"
    # Verify that the expected triples are present in the graph
    expected_graph = Graph()
    expected_ttl_data = """
        @prefix amor-exp: <http://www.gsi.upm.es/ontologies/amor/experiments/ns#> .
        @prefix amor-exec: <http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#> .
        
        amor-exec:exp1 a amor-exp:Experiment ;
            amor-exp:hasExecutor amor-exec:ari41 ;
            amor-exp:hasRequester amor-exec:researcher1 ;
            amor-exp:hasExperimentationSubject amor-exec:user_moralbias_001 .
    """
    expected_graph.parse(data=expected_ttl_data, format="turtle")

    # Compare the two graphs
    assert len(graph) == len(expected_graph), f"Graph lengths differ: expected {len(expected_graph)}, got {len(graph)}"

    for triple in expected_graph:
        assert triple in graph, f"Expected triple {triple} is missing in the graph"

    for triple in graph:
        assert triple in expected_graph, f"Unexpected triple {triple} found in the graph"

def test_GET_experiment_uri_params():
    # Test the /experiments endpoint
    
    # Insert a log entry to populate the SEGB
    url = f"{BASE_URL}/log"
    headers = {
        "Content-Type": "text/turtle",
        "Authorization": f"Bearer {LOGGER_TOKEN}"
    }
    
    # Example TTL data for experiments
    ttl_data = """
        @prefix amor-exp: <http://www.gsi.upm.es/ontologies/amor/experiments/ns#> .
        @prefix amor-exec: <http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#> .
        
        amor-exec:exp1 a amor-exp:Experiment ;
            amor-exp:hasExecutor amor-exec:ari41 ;
            amor-exp:hasRequester amor-exec:researcher1 ;
            amor-exp:hasExperimentationSubject amor-exec:user_moralbias_001 .
        amor-exec:exp2 a amor-exp:Experiment ;
            amor-exp:hasExecutor amor-exec:ari42 ;
            amor-exp:hasRequester amor-exec:researcher2 ;
            amor-exp:hasExperimentationSubject amor-exec:user_moralbias_002 .
        amor-exec:exp3 a amor-exp:Experiment ;
            amor-exp:hasExecutor amor-exec:ari43 ;
            amor-exp:hasExperimentationSubject amor-exec:user_moralbias_002 .
        amor-exec:exp4 a amor-exp:Experiment ;
            amor-exp:hasRequester amor-exec:researcher2 ;
            amor-exp:hasExperimentationSubject amor-exec:user_moralbias_002 .
    """
    response = requests.post(url, headers=headers, data=ttl_data)
    assert response.status_code == 201, f"Expected HTTP 201 Created code when inserting log, but got {response.status_code}"
    
    # Test the get /experiments endpoint    
    url = f"{BASE_URL}/experiments"
    headers = {
        "Authorization": f"Bearer {READER_TOKEN}"
    }
    params = {
        "uri": "http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#exp1"
    }
    response = requests.get(url, headers=headers, params=params)
    
    assert response.status_code == 200, f"Expected HTTP 200 OK code, but got {response.status_code}"
    
    # Load the response into an RDFLib graph
    graph = Graph()
    graph.parse(data=response.text, format="turtle")


    # Log all triples in the graph
    for subj, pred, obj in graph:
        logger.debug(f"Triple found:\n{subj} {pred} {obj}")
    # Verify that the graph is not empty
    assert len(graph) > 0, "The RDF graph is empty"
    # Verify that the expected triples are present in the graph
    expected_graph = Graph()
    expected_ttl_data = """
        @prefix amor-exp: <http://www.gsi.upm.es/ontologies/amor/experiments/ns#> .
        @prefix amor-exec: <http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#> .
        
        amor-exec:exp1 a amor-exp:Experiment ;
            amor-exp:hasExecutor amor-exec:ari41 ;
            amor-exp:hasRequester amor-exec:researcher1 ;
            amor-exp:hasExperimentationSubject amor-exec:user_moralbias_001 .
    """
    expected_graph.parse(data=expected_ttl_data, format="turtle")

    # Compare the two graphs
    assert len(graph) == len(expected_graph), f"Graph lengths differ: expected {len(expected_graph)}, got {len(graph)}"

    for triple in expected_graph:
        assert triple in graph, f"Expected triple {triple} is missing in the graph"

    for triple in graph:
        assert triple in expected_graph, f"Unexpected triple {triple} found in the graph"

def test_GET_experiment_with_activities():
    # Test the /experiments endpoint
    
    # Insert a log entry to populate the SEGB
    url = f"{BASE_URL}/log"
    headers = {
        "Content-Type": "text/turtle",
        "Authorization": f"Bearer {LOGGER_TOKEN}"
    }
    
    # Example TTL data for experiments
    ttl_data = """
        @prefix amor-exp: <http://www.gsi.upm.es/ontologies/amor/experiments/ns#> .
        @prefix amor-exec: <http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#> .
        
        amor-exec:exp1 a amor-exp:Experiment ;
            amor-exp:hasExecutor amor-exec:ari41 ;
            amor-exp:hasRequester amor-exec:researcher1 ;
            amor-exp:hasExperimentationSubject amor-exec:user_moralbias_001 .
    """
    response = requests.post(url, headers=headers, data=ttl_data)
    assert response.status_code == 201, f"Expected HTTP 201 Created code when inserting log, but got {response.status_code}"
    
    ttl_data = """
        @prefix amor-exp: <http://www.gsi.upm.es/ontologies/amor/experiments/ns#> .
        @prefix amor-exec: <http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#> .
        @prefix segb: <http://www.gsi.upm.es/ontologies/segb/ns#> .
        @prefix oro: <http://kb.openrobots.org#> .
        @prefix prov: <http://www.w3.org/ns/prov#> .
        @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
        
        amor-exec:listeningEvent1 a oro:ListeningEvent, segb:LoggedActivity ;
            amor-exp:isRelatedWithExperiment amor-exec:exp1 ;
            oro:hasSpeaker amor-exec:maria ;
            oro:hasListener amor-exec:ari1 ;
            oro:hasMessage amor-exec:msg1 ;
            segb:usedMLModel amor-exec:asrModel1 ;
            prov:startedAtTime "2024-11-16T12:27:12"^^xsd:dateTime ;
            prov:endedAtTime "2024-11-16T12:27:15"^^xsd:dateTime ;
            segb:wasPerformedBy amor-exec:ari1 .

        amor-exec:msg1 a oro:InitialMessage, oro:Message, prov:Entity ;
            oro:hasText "Good morning, Ari. Could you show me news about the awful climate change the planet is undergoing?."@en ;
            prov:wasGeneratedBy amor-exec:listeningEvent1 .

        amor-exec:decisionMakingAction1 a oro:DecisionMakingAction, segb:LoggedActivity ;
            amor-exp:isRelatedWithExperiment amor-exec:exp1 ;
            segb:triggeredByActivity amor-exec:listeningEvent1 ;
            segb:triggeredByActivity amor-exec:detectedHumanEvent1 ;
            segb:usedMLModel amor-exec:decisionMakingModel1 ;
            prov:startedAtTime "2024-11-16T12:27:15"^^xsd:dateTime ;
            segb:wasPerformedBy amor-exec:ari1 .
    """
    response = requests.post(url, headers=headers, data=ttl_data)
    assert response.status_code == 201, f"Expected HTTP 201 Created code when inserting log, but got {response.status_code}"
    
    # Test the get /experiments endpoint    
    url = f"{BASE_URL}/experiments?namespace=http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns%23&experiment_id=exp1"
    headers = {
        "Authorization": f"Bearer {READER_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    
    assert response.status_code == 200, f"Expected HTTP 200 OK code, but got {response.status_code}"
    
    # Load the response into an RDFLib graph
    graph = Graph()
    graph.parse(data=response.text, format="turtle")
    # Write the resulting graph to a file
    output_file = "./test/logs/graph.ttl"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(graph.serialize(format="turtle"))
    logger.info(f"Graph written to {output_file}")
    # Log all triples in the graph
    for subj, pred, obj in graph:
        logger.debug(f"Triple found:\n{subj} {pred} {obj}")
    # Verify that the graph is not empty
    assert len(graph) > 0, "The RDF graph is empty"
    # Verify that the expected triples are present in the graph
    expected_graph = Graph()
    expected_ttl_data = """
        @prefix amor-exec: <http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#> .
        @prefix amor-exp: <http://www.gsi.upm.es/ontologies/amor/experiments/ns#> .
        @prefix oro: <http://kb.openrobots.org#> .
        @prefix prov: <http://www.w3.org/ns/prov#> .
        @prefix segb: <http://www.gsi.upm.es/ontologies/segb/ns#> .
        @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
        
        amor-exec:decisionMakingAction1 a oro:DecisionMakingAction,
                segb:LoggedActivity ;
            amor-exp:isRelatedWithExperiment amor-exec:exp1 ;
            segb:triggeredByActivity amor-exec:detectedHumanEvent1,
                amor-exec:listeningEvent1 ;
            segb:usedMLModel amor-exec:decisionMakingModel1 ;
            segb:wasPerformedBy amor-exec:ari1 ;
            prov:startedAtTime "2024-11-16T12:27:15"^^xsd:dateTime .
        
        amor-exec:listeningEvent1 a oro:ListeningEvent,
                segb:LoggedActivity ;
            oro:hasListener amor-exec:ari1 ;
            oro:hasMessage amor-exec:msg1 ;
            oro:hasSpeaker amor-exec:maria ;
            amor-exp:isRelatedWithExperiment amor-exec:exp1 ;
            segb:usedMLModel amor-exec:asrModel1 ;
            segb:wasPerformedBy amor-exec:ari1 ;
            prov:endedAtTime "2024-11-16T12:27:15"^^xsd:dateTime ;
            prov:startedAtTime "2024-11-16T12:27:12"^^xsd:dateTime .
        
        amor-exec:exp1 a amor-exp:Experiment ;
            amor-exp:hasExecutor amor-exec:ari41 ;
            amor-exp:hasExperimentationSubject amor-exec:user_moralbias_001 ;
            amor-exp:hasRequester amor-exec:researcher1 .
    """
    expected_graph.parse(data=expected_ttl_data, format="turtle")

    # Compare the two graphs
    assert len(graph) == len(expected_graph), f"Graph lengths differ: expected {len(expected_graph)}, got {len(graph)}"

    for triple in expected_graph:
        assert triple in graph, f"Expected triple {triple} is missing in the graph"

    for triple in graph:
        assert triple in expected_graph, f"Unexpected triple {triple} found in the graph"

def test_GET_experiment_non_existing_experiment_uri():
    # Test the /experiments endpoint
    
    # Insert a log entry to populate the SEGB
    url = f"{BASE_URL}/log"
    headers = {
        "Content-Type": "text/turtle",
        "Authorization": f"Bearer {LOGGER_TOKEN}"
    }
    
    # Example TTL data for experiments
    ttl_data = """
        @prefix amor-exp: <http://www.gsi.upm.es/ontologies/amor/experiments/ns#> .
        @prefix amor-exec: <http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#> .
        
        amor-exec:exp1 a amor-exp:Experiment ;
            amor-exp:hasExecutor amor-exec:ari41 ;
            amor-exp:hasRequester amor-exec:researcher1 ;
            amor-exp:hasExperimentationSubject amor-exec:user_moralbias_001 .
        amor-exec:exp2 a amor-exp:Experiment ;
            amor-exp:hasExecutor amor-exec:ari42 ;
            amor-exp:hasRequester amor-exec:researcher2 ;
            amor-exp:hasExperimentationSubject amor-exec:user_moralbias_002 .
        amor-exec:exp3 a amor-exp:Experiment ;
            amor-exp:hasExecutor amor-exec:ari43 ;
            amor-exp:hasExperimentationSubject amor-exec:user_moralbias_002 .
        amor-exec:exp4 a amor-exp:Experiment ;
            amor-exp:hasRequester amor-exec:researcher2 ;
            amor-exp:hasExperimentationSubject amor-exec:user_moralbias_002 .
    """
    response = requests.post(url, headers=headers, data=ttl_data)
    assert response.status_code == 201, f"Expected HTTP 201 Created code when inserting log, but got {response.status_code}"
    
    # Test the get /experiments endpoint
    url = f"{BASE_URL}/experiments?namespace=http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns&experiment_id=exp10"
    headers = {
        "Authorization": f"Bearer {READER_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    
    assert response.status_code == 404, f"Expected HTTP 404 Not Found, but got {response.status_code}"

def test_GET_experiment_missing_experiment():
    # Test the /experiments endpoint
    # Test the get experiments endpoint
    url = f"{BASE_URL}/experiments?namespace=http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns&experiment_id=exp1"
    headers = {
        "Authorization": f"Bearer {READER_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    assert response.status_code == 404, f"Expected HTTP 404 Not Found, but got {response.status_code}"

def test_GET_experiment_missing_experiment_id():
    # Test the /experiments endpoint
    # Test the get experiments endpoint
    url = f"{BASE_URL}/experiments?namespace=http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns"
    headers = {
        "Authorization": f"Bearer {READER_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    assert response.status_code == 422, f"Expected HTTP 422 Unprocessable Entity, but got {response.status_code}"

def test_GET_experiment_missing_namespace():
    # Test the /experiments endpoint
    # Test the get experiments endpoint
    url = f"{BASE_URL}/experiments?experiment_id=exp1"
    headers = {
        "Authorization": f"Bearer {READER_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    assert response.status_code == 422, f"Expected HTTP 422 Unprocessable Entity, but got {response.status_code}"

def test_GET_experiment_missing_namespace_and_experiment_id():
    # Test the /experiments endpoint
    # Test the get experiments endpoint
    url = f"{BASE_URL}/experiments"
    headers = {
        "Authorization": f"Bearer {READER_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    assert response.status_code == 204, f"Expected HTTP 204 No Content, but got {response.status_code}"

def test_GET_log_with_json_params():
    # Insert a log entry first
    url = f"{BASE_URL}/log"
    headers = {
        "Content-Type": "text/turtle",
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

def test_GET_experiment_with_json_params():
    # Insert a log entry to populate the SEGB
    url = f"{BASE_URL}/log"
    headers = {
        "Content-Type": "text/turtle",
        "Authorization": f"Bearer {LOGGER_TOKEN}"
    }
    
    # Example TTL data for experiments
    ttl_data = """
        @prefix amor-exp: <http://www.gsi.upm.es/ontologies/amor/experiments/ns#> .
        @prefix amor-exec: <http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#> .
        
        amor-exec:exp1 a amor-exp:Experiment ;
            amor-exp:hasExecutor amor-exec:ari41 ;
            amor-exp:hasRequester amor-exec:researcher1 ;
            amor-exp:hasExperimentationSubject amor-exec:user_moralbias_001 .
    """
    response = requests.post(url, headers=headers, data=ttl_data)
    assert response.status_code == 201, f"Expected HTTP 201 Created code when inserting log, but got {response.status_code}"
    
    # Test the get /experiments endpoint with JSON parameters
    url = f"{BASE_URL}/experiments"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {READER_TOKEN}"
    }
    json_data = {
        "namespace": "http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns",
        "experiment_id": "exp1"
    }
    with requests.get(url, headers=headers, json=json_data) as response:
        logger.debug(f"GET experiment response: {response.text}")

        assert response.status_code == 200, f"Expected HTTP 200 OK code, but got {response.status_code}"

        # Load the response into an RDFLib graph
        graph = Graph()
        graph.parse(data=response.text, format="turtle")
        # Verify that the graph is not empty
        assert len(graph) > 0, "The RDF graph is empty"
        # Verify that the expected triples are present in the graph
        expected_graph = Graph()
        expected_ttl_data = """
            @prefix amor-exp: <http://www.gsi.upm.es/ontologies/amor/experiments/ns#> .
            @prefix amor-exec: <http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#> .

            amor-exec:exp1 a amor-exp:Experiment ;
                amor-exp:hasExecutor amor-exec:ari41 ;
                amor-exp:hasRequester amor-exec:researcher1 ;
                amor-exp:hasExperimentationSubject amor-exec:user_moralbias_001 .
        """
        expected_graph.parse(data=expected_ttl_data, format="turtle")
        # Compare the two graphs
        assert len(graph) == len(expected_graph), f"Graph lengths differ: expected {len(expected_graph)}, got {len(graph)}"
        for triple in expected_graph:
            assert triple in graph, f"Expected triple {triple} is missing in the graph"
        for triple in graph:
            assert triple in expected_graph, f"Unexpected triple {triple} found in the graph"

def test_GET_experiment_with_json_params_hashtag_namespace():
    # Insert a log entry to populate the SEGB
    url = f"{BASE_URL}/log"
    headers = {
        "Content-Type": "text/turtle",
        "Authorization": f"Bearer {LOGGER_TOKEN}"
    }
    
    # Example TTL data for experiments
    ttl_data = """
        @prefix amor-exp: <http://www.gsi.upm.es/ontologies/amor/experiments/ns#> .
        @prefix amor-exec: <http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#> .
        
        amor-exec:exp1 a amor-exp:Experiment ;
            amor-exp:hasExecutor amor-exec:ari41 ;
            amor-exp:hasRequester amor-exec:researcher1 ;
            amor-exp:hasExperimentationSubject amor-exec:user_moralbias_001 .
    """
    response = requests.post(url, headers=headers, data=ttl_data)
    assert response.status_code == 201, f"Expected HTTP 201 Created code when inserting log, but got {response.status_code}"
    
    # Test the get /experiments endpoint with JSON parameters and namespace ending with a hashtag
    url = f"{BASE_URL}/experiments"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {READER_TOKEN}"
    }
    json_data = {
        "namespace": "http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#",
        "experiment_id": "exp1"
    }
    response = requests.get(url, headers=headers, json=json_data)
    
    assert response.status_code == 200, f"Expected HTTP 200 OK code, but got {response.status_code}"
    
    # Load the response into an RDFLib graph
    graph = Graph()
    graph.parse(data=response.text, format="turtle")
    # Verify that the graph is not empty
    assert len(graph) > 0, "The RDF graph is empty"
    # Verify that the expected triples are present in the graph
    expected_graph = Graph()
    expected_ttl_data = """
        @prefix amor-exp: <http://www.gsi.upm.es/ontologies/amor/experiments/ns#> .
        @prefix amor-exec: <http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#> .
        
        amor-exec:exp1 a amor-exp:Experiment ;
            amor-exp:hasExecutor amor-exec:ari41 ;
            amor-exp:hasRequester amor-exec:researcher1 ;
            amor-exp:hasExperimentationSubject amor-exec:user_moralbias_001 .
    """
    expected_graph.parse(data=expected_ttl_data, format="turtle")
    # Compare the two graphs
    assert len(graph) == len(expected_graph), f"Graph lengths differ: expected {len(expected_graph)}, got {len(graph)}"
    for triple in expected_graph:
        assert triple in graph, f"Expected triple {triple} is missing in the graph"
    for triple in graph:
        assert triple in expected_graph, f"Unexpected triple {triple} found in the graph"
    assert len(graph) == len(expected_graph), f"Graph lengths differ: expected {len(expected_graph)}, got {len(graph)}"

def test_GET_experiment_with_json_params_uri():
    # Insert a log entry to populate the SEGB
    url = f"{BASE_URL}/log"
    headers = {
        "Content-Type": "text/turtle",
        "Authorization": f"Bearer {LOGGER_TOKEN}"
    }
    
    # Example TTL data for experiments
    ttl_data = """
        @prefix amor-exp: <http://www.gsi.upm.es/ontologies/amor/experiments/ns#> .
        @prefix amor-exec: <http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#> .
        
        amor-exec:exp1 a amor-exp:Experiment ;
            amor-exp:hasExecutor amor-exec:ari41 ;
            amor-exp:hasRequester amor-exec:researcher1 ;
            amor-exp:hasExperimentationSubject amor-exec:user_moralbias_001 .
    """
    response = requests.post(url, headers=headers, data=ttl_data)
    assert response.status_code == 201, f"Expected HTTP 201 Created code when inserting log, but got {response.status_code}"
    
    # Test the get experiments endpoint with JSON parameters and namespace ending with a hashtag
    url = f"{BASE_URL}/experiments"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {READER_TOKEN}"
    }
    json_data = {
        "uri": "http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#exp1"
    }
    response = requests.get(url, headers=headers, json=json_data)
    
    assert response.status_code == 200, f"Expected HTTP 200 OK code, but got {response.status_code}"
    
    # Load the response into an RDFLib graph
    graph = Graph()
    graph.parse(data=response.text, format="turtle")
    # Verify that the graph is not empty
    assert len(graph) > 0, "The RDF graph is empty"
    # Verify that the expected triples are present in the graph
    expected_graph = Graph()
    expected_ttl_data = """
        @prefix amor-exp: <http://www.gsi.upm.es/ontologies/amor/experiments/ns#> .
        @prefix amor-exec: <http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#> .
        
        amor-exec:exp1 a amor-exp:Experiment ;
            amor-exp:hasExecutor amor-exec:ari41 ;
            amor-exp:hasRequester amor-exec:researcher1 ;
            amor-exp:hasExperimentationSubject amor-exec:user_moralbias_001 .
    """
    expected_graph.parse(data=expected_ttl_data, format="turtle")
    # Compare the two graphs
    assert len(graph) == len(expected_graph), f"Graph lengths differ: expected {len(expected_graph)}, got {len(graph)}"
    for triple in expected_graph:
        assert triple in graph, f"Expected triple {triple} is missing in the graph"
    for triple in graph:
        assert triple in expected_graph, f"Unexpected triple {triple} found in the graph"
    assert len(graph) == len(expected_graph), f"Graph lengths differ: expected {len(expected_graph)}, got {len(graph)}"

def test_check_auth_admin_level():
    # IMPORTANT: Empty DB, so HTTP responses could be different as expected
    if not SECRET_KEY:
        pytest.skip("Skipping test because the server is not secured")
    
    ### TESTING AUTHORIZATION LEVELS FOR GET /history ###
    url = f"{BASE_URL}/history"
    
    # Test that accessing /history with ADMIN_TOKEN is allowed
    headers = {
        "Authorization": f"Bearer {ADMIN_TOKEN}"
    }
    history_response = requests.get(url, headers=headers)
    assert history_response.status_code == 204, f"Expected HTTP 204 when access /history with ADMIN_TOKEN, but got {history_response.status_code}"

    # Test that accessing /history with READER_TOKEN is forbidden
    headers = {
        "Authorization": f"Bearer {READER_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    assert response.status_code == 403, f"Expected HTTP 403 Forbidden for READER_TOKEN, but got {response.status_code}"

    # Test that accessing /history with LOGGER_TOKEN is forbidden
    headers = {
        "Authorization": f"Bearer {LOGGER_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    assert response.status_code == 403, f"Expected HTTP 403 Forbidden for LOGGER_TOKEN, but got {response.status_code}"
    
    # Test that accessing /history without token is forbidden
    response = requests.get(url)
    assert response.status_code == 401, f"Expected HTTP 401 Unauthorized for no token, but got {response.status_code}"
    
    
    ### TESTING AUTHORIZATION LEVELS FOR GET /log ###
    # Use the log_id in the URL
    url = f"{BASE_URL}/log?log_id=any"
    # Test that accessing /log with ADMIN_TOKEN is allowed
    headers = {
        "Authorization": f"Bearer {ADMIN_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    assert response.status_code == 404, f"Expected HTTP 404 Not Found for ADMIN_TOKEN, but got {response.status_code}"

    # Test that accessing /log with READER_TOKEN is forbidden
    headers = {
        "Authorization": f"Bearer {READER_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    assert response.status_code == 403, f"Expected HTTP 403 Forbidden for READER_TOKEN, but got {response.status_code}"

    # Test that accessing /log with LOGGER_TOKEN is forbidden
    headers = {
        "Authorization": f"Bearer {LOGGER_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    assert response.status_code == 403, f"Expected HTTP 403 Forbidden for LOGGER_TOKEN, but got {response.status_code}"

    # Test that accessing /log without token is forbidden
    response = requests.get(url)
    assert response.status_code == 401, f"Expected HTTP 401 Unauthorized for no token, but got {response.status_code}"
    
    
    ### TESTING AUTHORIZATION LEVELS FOR DELETE /graph ###
    url = f"{BASE_URL}/graph"
    # Test that deleting /graph with ADMIN_TOKEN is allowed
    headers = {
        "Authorization": f"Bearer {ADMIN_TOKEN}"
    }
    response = requests.delete(url, headers=headers)
    assert response.status_code == 204, f"Expected HTTP 204 when access /graph with ADMIN_TOKEN, but got {response.status_code}"
    
    # Test that deleting /graph with READER_TOKEN is forbidden
    headers = {
        "Authorization": f"Bearer {READER_TOKEN}"
    }
    response = requests.delete(url, headers=headers)
    assert response.status_code == 403, f"Expected HTTP 403 Forbidden for READER_TOKEN, but got {response.status_code}"
    
    # Test that deleting /graph with LOGGER_TOKEN is forbidden
    headers = {
        "Authorization": f"Bearer {LOGGER_TOKEN}"
    }
    response = requests.delete(url, headers=headers)
    assert response.status_code == 403, f"Expected HTTP 403 Forbidden for LOGGER_TOKEN, but got {response.status_code}"
    
    # Test that deleting /graph without token is forbidden
    response = requests.delete(url)
    assert response.status_code == 401, f"Expected HTTP 401 Unauthorized for no token, but got {response.status_code}"
    
    
    ### TESTING AUTHORIZATION LEVELS FOR GET /query ###
    url = f"{BASE_URL}/query"
    # Test that accessing /query with ADMIN_TOKEN is allowed
    headers = {
        "Authorization": f"Bearer {ADMIN_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    assert response.status_code == 501, f"Expected HTTP 501 Not Implemented for ADMIN_TOKEN, but got {response.status_code}"
    
    # Test that accessing /query with READER_TOKEN is forbidden
    headers = {
        "Authorization": f"Bearer {READER_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    assert response.status_code == 403, f"Expected HTTP 403 Forbidden for READER_TOKEN, but got {response.status_code}"
    
    # Test that accessing /query with LOGGER_TOKEN is forbidden
    headers = {
        "Authorization": f"Bearer {LOGGER_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    assert response.status_code == 403, f"Expected HTTP 403 Forbidden for LOGGER_TOKEN, but got {response.status_code}"
    
    # Test that accessing /query without token is forbidden
    response = requests.get(url)
    assert response.status_code == 401, f"Expected HTTP 401 Unauthorized for no token, but got {response.status_code}"

def test_check_auth_reader_level():
    # IMPORTANT: Empty DB, so HTTP responses could be different as expected
    if not SECRET_KEY:
        pytest.skip("Skipping test because the server is not secured")
    
    ### TESTING AUTHORIZATION LEVELS FOR GET /graph ###
    
    # Test that accessing /graph with ADMIN_TOKEN is allowed
    url = f"{BASE_URL}/graph"
    headers = {
        "Authorization": f"Bearer {ADMIN_TOKEN}"
    }
    history_response = requests.get(url, headers=headers)
    assert history_response.status_code == 204, f"Expected HTTP 204 when access /graph with ADMIN_TOKEN, but got {history_response.status_code}"

    # Test that accessing /graph with READER_TOKEN is allowed
    headers = {
        "Authorization": f"Bearer {READER_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    assert response.status_code == 204, f"Expected HTTP 204 when access /graph with READER_TOKEN, but got {response.status_code}"

    # Test that accessing /graph with LOGGER_TOKEN is forbidden
    headers = {
        "Authorization": f"Bearer {LOGGER_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    assert response.status_code == 403, f"Expected HTTP 403 Forbidden for LOGGER_TOKEN, but got {response.status_code}"
    
    # Test that accessing /graph without token is forbidden
    response = requests.get(url)
    assert response.status_code == 401, f"Expected HTTP 401 Unauthorized for no token, but got {response.status_code}"
    
    
    ### TESTING AUTHORIZATION LEVELS FOR GET /experiments ###
    # Use the /experiments endpoint with specific parameters
    url = f"{BASE_URL}/experiments?namespace=http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns&experiment_id=exp1"
    # Test that accessing /experiments with ADMIN_TOKEN is allowed
    headers = {
        "Authorization": f"Bearer {ADMIN_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    assert response.status_code == 404, f"Expected HTTP 404 OK for ADMIN_TOKEN, but got {response.status_code}"
    
    # Test that accessing /experiments with READER_TOKEN is allowed
    headers = {
        "Authorization": f"Bearer {READER_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    assert response.status_code == 404, f"Expected HTTP 404 OK for READER_TOKEN, but got {response.status_code}"
    
    # Test that accessing /experiments with LOGGER_TOKEN is forbidden
    headers = {
        "Authorization": f"Bearer {LOGGER_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    assert response.status_code == 403, f"Expected HTTP 403 Forbidden for LOGGER_TOKEN, but got {response.status_code}"
    
    # Test that accessing /experiments without token is forbidden
    response = requests.get(url)
    assert response.status_code == 401, f"Expected HTTP 401 Unauthorized for no token, but got {response.status_code}"
    
    
    ### TESTING AUTHORIZATION LEVELS FOR GET /experiments ###
    url = f"{BASE_URL}/experiments"
    # Test that accessing /experiments with ADMIN_TOKEN is allowed
    headers = {
        "Authorization": f"Bearer {ADMIN_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    assert response.status_code == 204, f"Expected HTTP 204 when access /experiments with ADMIN_TOKEN, but got {response.status_code}"
    
    # Test that accessing /experiments with READER_TOKEN is allowed
    headers = {
        "Authorization": f"Bearer {READER_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    assert response.status_code == 204, f"Expected HTTP 204 when access /experiments with READER_TOKEN, but got {response.status_code}"
    
    # Test that accessing /experiments with LOGGER_TOKEN is forbidden
    headers = {
        "Authorization": f"Bearer {LOGGER_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    assert response.status_code == 403, f"Expected HTTP 403 Forbidden for LOGGER_TOKEN, but got {response.status_code}"
    
    # Test that accessing /graph without token is forbidden
    response = requests.get(url)
    assert response.status_code == 401, f"Expected HTTP 401 Unauthorized for no token, but got {response.status_code}"

def test_check_auth_logger_level():
    
    # IMPORTANT: Empty DB, so HTTP responses could be different as expected
    if not SECRET_KEY:
        pytest.skip("Skipping test because the server is not secured")
    
    ### TESTING AUTHORIZATION LEVELS FOR POST /log ###
    url = f"{BASE_URL}/log"
    # Test that inserting log with ADMIN_TOKEN is allowed# Test that accessing /log with ADMIN_TOKEN is allowed
    headers = {
        "Authorization": f"Bearer {ADMIN_TOKEN}"
    }
    response = requests.post(url, headers=headers)
    assert response.status_code == 400, f"Expected HTTP 400 Bad Request for ADMIN_TOKEN, but got {response.status_code}"

    # Test that accessing /log with READER_TOKEN is forbidden
    headers = {
        "Authorization": f"Bearer {READER_TOKEN}"
    }
    response = requests.post(url, headers=headers)
    assert response.status_code == 403, f"Expected HTTP 403 Forbidden for READER_TOKEN, but got {response.status_code}"

    # Test that accessing /log with LOGGER_TOKEN is forbidden
    headers = {
        "Authorization": f"Bearer {LOGGER_TOKEN}"
    }
    response = requests.post(url, headers=headers)
    assert response.status_code == 400, f"Expected HTTP 400 Bad Request for LOGGER_TOKEN, but got {response.status_code}"

    # Test that accessing /log without token is forbidden
    response = requests.post(url)
    assert response.status_code == 401, f"Expected HTTP 401 Unauthorized for no token, but got {response.status_code}"
