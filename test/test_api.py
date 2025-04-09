import pytest

from rdflib import Graph
import requests
import docker
import subprocess
import jwt
import logging
import os

# Set up logging
from dotenv import dotenv_values
# Load environment variables from a .env file
ENV_FILE = "./test/test.env"
# Load environment variables from the .env file without overriding existing ones in the environment
CONFIG = dotenv_values(ENV_FILE)

logging_level = CONFIG.get("LOGGING_LEVEL", "DEBUG").upper()
log_file = CONFIG.get("TESTS_LOG_FILE", "test_segb.log")
compose_file = CONFIG.get("COMPOSE_FILE", "./test/docker-compose.test.yaml")
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
logger.info(f"Using env_file: {ENV_FILE}")

logger.debug(f"For paths, checking working directory: {os.getcwd()}")
BASE_URL = CONFIG.get("BASE_URL", "http://127.0.0.1:5000")
TEST_DB_VOLUME = CONFIG.get("TEST_DB_VOLUME", "amor-segb-db-test")

logger.info(f"Loading test tokens from environment variables")
AUDITOR_TOKEN = CONFIG.get("AUDITOR_TOKEN", "fake_auditor_token")
LOGGER_TOKEN = CONFIG.get("LOGGER_TOKEN", "fake_logger_token")
ADMIN_TOKEN = CONFIG.get("ADMIN_TOKEN", "fake_admin_token")
AUDITOR_LOGGER_TOKEN = CONFIG.get("AUDITOR_LOGGER_TOKEN", "fake_auditor_logger_token")
ALL_ROLES_TOKEN = CONFIG.get("ALL_ROLES_TOKEN", "fake_all_roles_token")

logger.debug(f"AUDITOR_TOKEN: {AUDITOR_TOKEN}")
logger.debug(f"LOGGER_TOKEN: {LOGGER_TOKEN}")
logger.debug(f"ADMIN_TOKEN: {ADMIN_TOKEN}")
logger.debug(f"AUDITOR_LOGGER_TOKEN: {AUDITOR_LOGGER_TOKEN}")
logger.debug(f"ALL_ROLES_TOKEN: {ALL_ROLES_TOKEN}")

SECRET_KEY = CONFIG.get("SECRET_KEY", None)

logger.debug(f"SECRET_KEY: {SECRET_KEY}")

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
        "Content-Type": "text/turtle; charset=utf-8",
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
        "Content-Type": "text/turtle; charset=utf-8",
        "Authorization": f"Bearer {LOGGER_TOKEN}"
    }
    
    ttl_data = """
        @prefix ex: <http://example.org/> .
        ex:subject ex:predicate "object" .
    """
    response = requests.post(url, headers=headers, data=ttl_data)
    
    assert response.status_code == 201, f"Expected HTTP 201 Created code, but got {response.status_code}"

def test_POST_log_valid_data_with_auditor_token():
    url = f"{BASE_URL}/log"
    headers = {
        "Content-Type": "text/turtle; charset=utf-8",
        "Authorization": f"Bearer {AUDITOR_TOKEN}"
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
        "Content-Type": "text/turtle; charset=utf-8",
        "Authorization": f"Bearer {LOGGER_TOKEN}"
    }
    invalid_ttl_data = """
        prefix ex: http://example.org/> .
        ex:subject predicate "object" .
    """
    response = requests.post(url, headers=headers, data=invalid_ttl_data)
    
    assert response.status_code == 422, f"Expected HTTP 422 Unprocessable Entity code, but got {response.status_code}"

def test_POST_log_invalid_header_media_type_no_encoding():
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

def test_POST_log_invalid_header_media_type():
    url = f"{BASE_URL}/log"
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {LOGGER_TOKEN}"
    }
    ttl_data = """
        @prefix ex: <http://example.org/> .
        ex:subject ex:predicate "object" .
    """
    response = requests.post(url, headers=headers, data=ttl_data)
    
    assert response.status_code == 422, f"Expected HTTP 422 Unprocessable Entity code, but got {response.status_code}"

def test_POST_log_invalid_no_header_media_type():
    url = f"{BASE_URL}/log"
    headers = {
        "Authorization": f"Bearer {LOGGER_TOKEN}"
    }
    ttl_data = """
        @prefix ex: <http://example.org/> .
        ex:subject ex:predicate "object" .
    """
    response = requests.post(url, headers=headers, data=ttl_data)
    
    assert response.status_code == 422, f"Expected HTTP 422 Unprocessable Entity code, but got {response.status_code}"

def test_POST_log_no_data():
    url = f"{BASE_URL}/log"
    headers = {
        "Content-Type": "text/turtle; charset=utf-8",
        "Authorization": f"Bearer {LOGGER_TOKEN}"
    }
    response = requests.post(url, headers=headers)
    
    assert response.status_code == 422, f"Expected HTTP 422 Unprocessable Entity code, but got {response.status_code}"


def test_POST_log_empty_data():
    url = f"{BASE_URL}/log"
    headers = {
        "Content-Type": "text/turtle; charset=utf-8",
        "Authorization": f"Bearer {LOGGER_TOKEN}"
    }
    empty_data = ""
    response = requests.post(url, headers=headers, data=empty_data)
    
    assert response.status_code == 422, f"Expected HTTP 422 Unprocessable Entity code, but got {response.status_code}"

def test_GET_empty_graph():
    url = f"{BASE_URL}/graph"
    headers = {
        "Authorization": f"Bearer {AUDITOR_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    assert response.status_code == 204, f"Expected HTTP 204 Empty Content code, but got {response.status_code}"
    logger.debug(f"Response text: {response.text}")
    logger.debug(f"Response length: {len(response.text)}")
    assert response.text == "", f"Expected empty response, but got {response.text}"

def test_GET_graph_with_one_POST():
    
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
    assert response.status_code == 201, f"Expected HTTP 201 Created code, but got {response.status_code}"
    
    time.sleep(3)  # Wait for the data to be processed and available in the graph
    
    url = f"{BASE_URL}/graph"
    headers = {
        "Authorization": f"Bearer {AUDITOR_TOKEN}"
    }
    response = requests.get(url, headers=headers, stream=True)
    logger.debug(f"Response text: {response.text}")
    assert response.status_code == 200, f"Expected HTTP 200 OK code, but got {response.status_code}"
    assert "ex:subject ex:predicate \"object\" ." in response.text, "TTL data is missing in the response"
    assert "@prefix ex: <http://example.org/> ." in response.text, "@prefix is missing in the response"

def test_GET_graph_with_several_POST():

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
    assert response1.status_code == 201, f"Expected HTTP 201 Created code, but got {response1.status_code}"
    
    response2 = requests.post(url, headers=headers, data=ttl_data_2)
    assert response2.status_code == 201, f"Expected HTTP 201 Created code, but got {response2.status_code}"

    url = f"{BASE_URL}/graph"
    headers = {
        "Authorization": f"Bearer {AUDITOR_TOKEN}"
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
        "Content-Type": "text/turtle; charset=utf-8",
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

def test_GET_experiments_basic():
    # Test the /experiments endpoint
    
    # Insert a log entry to populate the SEGB
    url = f"{BASE_URL}/log"
    headers = {
        "Content-Type": "text/turtle; charset=utf-8",
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
        "Authorization": f"Bearer {AUDITOR_TOKEN}"
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
        "Content-Type": "text/turtle; charset=utf-8",
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
        "Authorization": f"Bearer {AUDITOR_TOKEN}"
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
        "Content-Type": "text/turtle; charset=utf-8",
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
        "Authorization": f"Bearer {AUDITOR_TOKEN}"
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
        "Authorization": f"Bearer {AUDITOR_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    assert response.status_code == 204, f"Expected HTTP 204 No Content code, but got {response.status_code}"

def test_GET_experiment():
    # Test the /experiments endpoint
    
    # Insert a log entry to populate the SEGB
    url = f"{BASE_URL}/log"
    headers = {
        "Content-Type": "text/turtle; charset=utf-8",
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
        "Authorization": f"Bearer {AUDITOR_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    
    assert response.status_code == 200, f"Expected HTTP 200 OK code, but got {response.status_code}"
    
    # Load the response into an RDFLib graph
    resulting_graph = Graph()
    resulting_graph.parse(data=response.text, format="turtle")
    # Verify that the graph is not empty
    assert len(resulting_graph) > 0, "The RDF graph is empty"
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
    assert len(resulting_graph) == len(expected_graph), f"Graph lengths differ: expected {len(expected_graph)}, got {len(resulting_graph)}"

    for triple in expected_graph:
        assert triple in resulting_graph, f"Expected triple {triple} is missing in the graph"

    for triple in resulting_graph:
        assert triple in expected_graph, f"Unexpected triple {triple} found in the graph"

def test_GET_experiment_query_hastag_code():
    # Test the /experiments endpoint
    
    # Insert a log entry to populate the SEGB
    url = f"{BASE_URL}/log"
    headers = {
        "Content-Type": "text/turtle; charset=utf-8",
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
        "Authorization": f"Bearer {AUDITOR_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    
    assert response.status_code == 200, f"Expected HTTP 200 OK code, but got {response.status_code}"
    
    # Load the response into an RDFLib graph
    resulting_graph = Graph()
    resulting_graph.parse(data=response.text, format="turtle")
    # Verify that the graph is not empty
    assert len(resulting_graph) > 0, "The RDF graph is empty"
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
    assert len(resulting_graph) == len(expected_graph), f"Graph lengths differ: expected {len(expected_graph)}, got {len(resulting_graph)}"

    for triple in expected_graph:
        assert triple in resulting_graph, f"Expected triple {triple} is missing in the graph"

    for triple in resulting_graph:
        assert triple in expected_graph, f"Unexpected triple {triple} found in the graph"

def test_GET_experiment_query_params():
    # Test the /experiments endpoint
    
    # Insert a log entry to populate the SEGB
    url = f"{BASE_URL}/log"
    headers = {
        "Content-Type": "text/turtle; charset=utf-8",
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
        "Authorization": f"Bearer {AUDITOR_TOKEN}"
    }
    params = {
        "experiment_id": "exp3",
        "namespace": "http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#"
    }
    response = requests.get(url, headers=headers, params=params)
    
    assert response.status_code == 200, f"Expected HTTP 200 OK code, but got {response.status_code}"
    
    # Load the response into an RDFLib graph
    resulting_graph = Graph()
    resulting_graph.parse(data=response.text, format="turtle")
    # Verify that the graph is not empty
    assert len(resulting_graph) > 0, "The RDF graph is empty"
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
    assert len(resulting_graph) == len(expected_graph), f"Graph lengths differ: expected {len(expected_graph)}, got {len(resulting_graph)}"

    for triple in expected_graph:
        assert triple in resulting_graph, f"Expected triple {triple} is missing in the graph"

    for triple in resulting_graph:
        assert triple in expected_graph, f"Unexpected triple {triple} found in the graph"

def test_GET_experiment_uri():
    # Test the /experiments endpoint
    
    # Insert a log entry to populate the SEGB
    url = f"{BASE_URL}/log"
    headers = {
        "Content-Type": "text/turtle; charset=utf-8",
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
        "Authorization": f"Bearer {AUDITOR_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    
    assert response.status_code == 200, f"Expected HTTP 200 OK code, but got {response.status_code}"
    
    # Load the response into an RDFLib graph
    resulting_graph = Graph()
    resulting_graph.parse(data=response.text, format="turtle")
    # Verify that the graph is not empty
    assert len(resulting_graph) > 0, "The RDF graph is empty"
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
    assert len(resulting_graph) == len(expected_graph), f"Graph lengths differ: expected {len(expected_graph)}, got {len(resulting_graph)}"

    for triple in expected_graph:
        assert triple in resulting_graph, f"Expected triple {triple} is missing in the graph"

    for triple in resulting_graph:
        assert triple in expected_graph, f"Unexpected triple {triple} found in the graph"


def test_GET_experiment_uri_malformed_invalid_uri():
    # Test the /experiments endpoint
    
    # Insert a log entry to populate the SEGB
    url = f"{BASE_URL}/log"
    headers = {
        "Content-Type": "text/turtle; charset=utf-8",
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
    url = f"{BASE_URL}/experiments?uri=http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns/exp1"
    headers = {
        "Authorization": f"Bearer {AUDITOR_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    
    assert response.status_code == 422, f"Expected HTTP 422 Unprocessable Entity code, but got {response.status_code}"
        
def test_GET_experiment_uri_params():
    # Test the /experiments endpoint
    
    # Insert a log entry to populate the SEGB
    url = f"{BASE_URL}/log"
    headers = {
        "Content-Type": "text/turtle; charset=utf-8",
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
        "Authorization": f"Bearer {AUDITOR_TOKEN}"
    }
    params = {
        "uri": "http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#exp1"
    }
    response = requests.get(url, headers=headers, params=params)
    
    assert response.status_code == 200, f"Expected HTTP 200 OK code, but got {response.status_code}"
    
    # Load the response into an RDFLib graph
    resulting_graph = Graph()
    resulting_graph.parse(data=response.text, format="turtle")
    # Verify that the graph is not empty
    assert len(resulting_graph) > 0, "The RDF graph is empty"
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
    assert len(resulting_graph) == len(expected_graph), f"Graph lengths differ: expected {len(expected_graph)}, got {len(resulting_graph)}"

    for triple in expected_graph:
        assert triple in resulting_graph, f"Expected triple {triple} is missing in the graph"

    for triple in resulting_graph:
        assert triple in expected_graph, f"Unexpected triple {triple} found in the graph"

def test_GET_experiment_with_activities():
    # Test the /experiments endpoint
    
    # Insert a log entry to populate the SEGB
    url = f"{BASE_URL}/log"
    headers = {
        "Content-Type": "text/turtle; charset=utf-8",
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
        "Authorization": f"Bearer {AUDITOR_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    
    assert response.status_code == 200, f"Expected HTTP 200 OK code, but got {response.status_code}"
    
    # Load the response into an RDFLib graph
    resulting_graph = Graph()
    resulting_graph.parse(data=response.text, format="turtle")
    # Verify that the graph is not empty
    assert len(resulting_graph) > 0, "The RDF graph is empty"
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

        amor-exec:msg1 a oro:InitialMessage, oro:Message, prov:Entity ;
            oro:hasText "Good morning, Ari. Could you show me news about the awful climate change the planet is undergoing?."@en ;
            prov:wasGeneratedBy amor-exec:listeningEvent1 .
        
        amor-exec:exp1 a amor-exp:Experiment ;
            amor-exp:hasExecutor amor-exec:ari41 ;
            amor-exp:hasExperimentationSubject amor-exec:user_moralbias_001 ;
            amor-exp:hasRequester amor-exec:researcher1 .
    """
    expected_graph.parse(data=expected_ttl_data, format="turtle")

    # Compare the two graphs
    assert len(resulting_graph) == len(expected_graph), f"Graph lengths differ: expected {len(expected_graph)}, got {len(resulting_graph)}"

    for triple in expected_graph:
        assert triple in resulting_graph, f"Expected triple {triple} is missing in the graph"

    for triple in resulting_graph:
        assert triple in expected_graph, f"Unexpected triple {triple} found in the graph"

def test_GET_experiment_with_activities_but_no_msgs():
    # Test the /experiments endpoint
    
    # Insert a log entry to populate the SEGB
    url = f"{BASE_URL}/log"
    headers = {
        "Content-Type": "text/turtle; charset=utf-8",
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
        "Authorization": f"Bearer {AUDITOR_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    
    assert response.status_code == 200, f"Expected HTTP 200 OK code, but got {response.status_code}"
    
    # Load the response into an RDFLib graph
    resulting_graph = Graph()
    resulting_graph.parse(data=response.text, format="turtle")
    # Verify that the graph is not empty
    assert len(resulting_graph) > 0, "The RDF graph is empty"
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
    assert len(resulting_graph) == len(expected_graph), f"Graph lengths differ: expected {len(expected_graph)}, got {len(resulting_graph)}"

    for triple in expected_graph:
        assert triple in resulting_graph, f"Expected triple {triple} is missing in the graph"

    for triple in resulting_graph:
        assert triple in expected_graph, f"Unexpected triple {triple} found in the graph"

def test_GET_experiment_non_existing_experiment_uri():
    # Test the /experiments endpoint
    
    # Insert a log entry to populate the SEGB
    url = f"{BASE_URL}/log"
    headers = {
        "Content-Type": "text/turtle; charset=utf-8",
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
        "Authorization": f"Bearer {AUDITOR_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    
    assert response.status_code == 404, f"Expected HTTP 404 Not Found, but got {response.status_code}"

def test_GET_experiment_missing_experiment():
    # Test the /experiments endpoint
    # Test the get experiments endpoint
    url = f"{BASE_URL}/experiments?namespace=http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns&experiment_id=exp1"
    headers = {
        "Authorization": f"Bearer {AUDITOR_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    assert response.status_code == 404, f"Expected HTTP 404 Not Found, but got {response.status_code}"

def test_GET_experiment_missing_experiment_id():
    # Test the /experiments endpoint
    # Test the get experiments endpoint
    url = f"{BASE_URL}/experiments?namespace=http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns"
    headers = {
        "Authorization": f"Bearer {AUDITOR_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    assert response.status_code == 422, f"Expected HTTP 422 Unprocessable Entity, but got {response.status_code}"

def test_GET_experiment_missing_namespace():
    # Test the /experiments endpoint
    # Test the get experiments endpoint
    url = f"{BASE_URL}/experiments?experiment_id=exp1"
    headers = {
        "Authorization": f"Bearer {AUDITOR_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    assert response.status_code == 422, f"Expected HTTP 422 Unprocessable Entity, but got {response.status_code}"

def test_GET_experiment_missing_namespace_and_experiment_id():
    # Test the /experiments endpoint
    # Test the get experiments endpoint
    url = f"{BASE_URL}/experiments"
    headers = {
        "Authorization": f"Bearer {AUDITOR_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    assert response.status_code == 204, f"Expected HTTP 204 No Content, but got {response.status_code}"

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

def test_GET_experiment_with_json_params():
    '''
    Test the GET /experiments endpoint with JSON parameters.
    This test performs the following steps:
    1. Inserts a log entry into the SEGB using a POST request with Turtle (TTL) data.
    2. Sends a GET request to the /experiments endpoint with JSON parameters specifying
       the namespace and experiment ID.
    3. Verifies that the response status code is 200 (HTTP OK).
    4. Parses the response JSON and validates that the returned experiment URIs match
       the expected URIs.
    5. Ensures that no unexpected URIs are present in the response.
    Note:
    - By convention, GET methods should not include a JSON body. In this case, the JSON
      body is ignored, and the endpoint behaves as if no parameters were provided,
      returning the list of experiments as it would for a GET /experiments request
      without parameters.
    '''
    # Insert a log entry to populate the SEGB
    url = f"{BASE_URL}/log"
    headers = {
        "Content-Type": "text/turtle; charset=utf-8",
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
        "Authorization": f"Bearer {AUDITOR_TOKEN}"
    }
    json_data = {
        "namespace": "http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns",
        "experiment_id": "exp1"
    }
    with requests.get(url, headers=headers, json=json_data) as response:
        logger.debug(f"GET experiment response: {response.text}")

    assert response.status_code == 200, f"Expected HTTP 200 OK code, but got {response.status_code}"

    # Parse the response JSON and verify the experiment URIs
    resulting_uris = response.json()
    expected_uris = [
        "http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#exp1",
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

def test_GET_experiment_with_json_params_hashtag_namespace():
    '''
    Test the GET /experiments endpoint with JSON parameters.
    This test performs the following steps:
    1. Inserts a log entry into the SEGB using a POST request with Turtle (TTL) data.
    2. Sends a GET request to the /experiments endpoint with JSON parameters specifying
       the namespace and experiment ID.
    3. Verifies that the response status code is 200 (HTTP OK).
    4. Parses the response JSON and validates that the returned experiment URIs match
       the expected URIs.
    5. Ensures that no unexpected URIs are present in the response.
    Note:
    - By convention, GET methods should not include a JSON body. In this case, the JSON
      body is ignored, and the endpoint behaves as if no parameters were provided,
      returning the list of experiments as it would for a GET /experiments request
      without parameters.
    '''
    # Insert a log entry to populate the SEGB
    url = f"{BASE_URL}/log"
    headers = {
        "Content-Type": "text/turtle; charset=utf-8",
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
        "Authorization": f"Bearer {AUDITOR_TOKEN}"
    }
    json_data = {
        "namespace": "http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#",
        "experiment_id": "exp1"
    }
    response = requests.get(url, headers=headers, json=json_data)
    
    assert response.status_code == 200, f"Expected HTTP 200 OK code, but got {response.status_code}"
    
    # Parse the response JSON and verify the experiment URIs
    resulting_uris = response.json()
    expected_uris = [
        "http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#exp1",
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

def test_GET_experiment_with_json_params_uri():
    '''
    Test the GET /experiments endpoint with JSON parameters.
    This test performs the following steps:
    1. Inserts a log entry into the SEGB using a POST request with Turtle (TTL) data.
    2. Sends a GET request to the /experiments endpoint with JSON parameters specifying
       the namespace and experiment ID.
    3. Verifies that the response status code is 200 (HTTP OK).
    4. Parses the response JSON and validates that the returned experiment URIs match
       the expected URIs.
    5. Ensures that no unexpected URIs are present in the response.
    Note:
    - By convention, GET methods should not include a JSON body. In this case, the JSON
      body is ignored, and the endpoint behaves as if no parameters were provided,
      returning the list of experiments as it would for a GET /experiments request
      without parameters.
    '''
    # Insert a log entry to populate the SEGB
    url = f"{BASE_URL}/log"
    headers = {
        "Content-Type": "text/turtle; charset=utf-8",
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
        "Authorization": f"Bearer {AUDITOR_TOKEN}"
    }
    json_data = {
        "uri": "http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#exp1"
    }
    response = requests.get(url, headers=headers, json=json_data)
    
    assert response.status_code == 200, f"Expected HTTP 200 OK code, but got {response.status_code}"
    
    # Parse the response JSON and verify the experiment URIs
    resulting_uris = response.json()
    expected_uris = [
        "http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#exp1",
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

def check_endpoints(endpoints_dict: dict, token_name: str, token: str):
    for endpoint, details in endpoints_dict.items():
        logger.debug(f"Testing {endpoint} endpoint for {token_name} level access")
        for method in details["methods"]:
            url = details["url"]
            headers = {"Authorization": f"Bearer {token}"}
            if method == "GET":
                response = requests.get(url, headers=headers)
            elif method == "POST":
                if endpoint == "log":
                    headers["Content-Type"] = "text/turtle; charset=utf-8"
                    response = requests.post(url, headers=headers, data=details["data"])
                else:
                    response = requests.post(url, headers=headers)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers)
            else:
                continue
            if isinstance(details["expected_response"], dict):
                expected_status = details["expected_response"].get(method)
                assert expected_status is not None, f"No expected response defined for method {method} on {url}"
            else:
                expected_status = details["expected_response"]

            logger.debug(f"Testing {method} {url} with token {token_name}")
            logger.debug(f"Response status code: {response.status_code}")
            logger.debug(f"Response text: {response.text}")
            assert response.status_code == expected_status, f"Expected HTTP {expected_status} for {method} {url}, but got {response.status_code}"
            
    logger.info(f"Completed testing all endpoints for {token_name} level access.")


def test_check_auth_admin_level():
    # IMPORTANT: Empty DB, so HTTP responses could be different as expected
    if not SECRET_KEY:
        pytest.skip("Skipping test because the server is not secured")
        
    token_name = "ADMIN"
    token = ADMIN_TOKEN
    
    endpoints_to_test = {
        "root": {
            "url": f"{BASE_URL}/",
            "methods": ["GET"],
            "expected_response": 200},
        "docs": {
            "url": f"{BASE_URL}/docs",
            "methods": ["GET"],
            "expected_response": 200},
        "health": {
            "url": f"{BASE_URL}/health",
            "methods": ["GET"],
            "expected_response": 200},
        "history": {
            "url": f"{BASE_URL}/history",
            "methods": ["GET"],
            "expected_response": 204},
        "log": {
            "url": f"{BASE_URL}/log",
            "methods": ["GET", "POST"],
            "expected_response": {"GET": 400, "POST": 422},
            "data": "invalid_ttl_data"},
        "graph": {
            "url": f"{BASE_URL}/graph",
            "methods": ["GET", "DELETE"],
            "expected_response": {"GET": 204, "DELETE": 204}},
        "query": {
            "url": f"{BASE_URL}/query",
            "methods": ["GET"], 
            "expected_response": 501},
        "experiments": {
            "url": f"{BASE_URL}/experiments",
            "methods": ["GET"],
            "expected_response": 204},
    }
    
    check_endpoints(endpoints_to_test, token_name, token)

def test_check_auth_auditor_level():
    # IMPORTANT: Empty DB, so HTTP responses could be different as expected
    if not SECRET_KEY:
        pytest.skip("Skipping test because the server is not secured")
        
    token_name = "AUDITOR"
    token = AUDITOR_TOKEN
    
    endpoints_to_test = {
        "root": {
            "url": f"{BASE_URL}/",
            "methods": ["GET"],
            "expected_response": 200},
        "docs": {
            "url": f"{BASE_URL}/docs",
            "methods": ["GET"],
            "expected_response": 200},
        "health": {
            "url": f"{BASE_URL}/health",
            "methods": ["GET"],
            "expected_response": 200},
        "history": {
            "url": f"{BASE_URL}/history",
            "methods": ["GET"],
            "expected_response": 204},
        "log": {
            "url": f"{BASE_URL}/log",
            "methods": ["GET", "POST"],
            "expected_response": {"GET": 400, "POST": 403},
            "data": "invalid_ttl_data"},
        "graph": {
            "url": f"{BASE_URL}/graph",
            "methods": ["GET", "DELETE"],
            "expected_response": {"GET": 204, "DELETE": 403}},
        "query": {
            "url": f"{BASE_URL}/query",
            "methods": ["GET"], 
            "expected_response": 403},
        "experiments": {
            "url": f"{BASE_URL}/experiments",
            "methods": ["GET"],
            "expected_response": 204},
    }
    
    check_endpoints(endpoints_to_test, token_name, token)

def test_check_auth_logger_level():
    # IMPORTANT: Empty DB, so HTTP responses could be different as expected
    if not SECRET_KEY:
        pytest.skip("Skipping test because the server is not secured")
        
    token_name = "LOGGER"
    token = LOGGER_TOKEN
    
    endpoints_to_test = {
        "root": {
            "url": f"{BASE_URL}/",
            "methods": ["GET"],
            "expected_response": 200},
        "docs": {
            "url": f"{BASE_URL}/docs",
            "methods": ["GET"],
            "expected_response": 200},
        "health": {
            "url": f"{BASE_URL}/health",
            "methods": ["GET"],
            "expected_response": 200},
        "history": {
            "url": f"{BASE_URL}/history",
            "methods": ["GET"],
            "expected_response": 403},
        "log": {
            "url": f"{BASE_URL}/log",
            "methods": ["GET", "POST"],
            "expected_response": {"GET": 403, "POST": 422},
            "data": "invalid_ttl_data"},
        "graph": {
            "url": f"{BASE_URL}/graph",
            "methods": ["GET", "DELETE"],
            "expected_response": {"GET": 403, "DELETE": 403}},
        "query": {
            "url": f"{BASE_URL}/query",
            "methods": ["GET"], 
            "expected_response": 403},
        "experiments": {
            "url": f"{BASE_URL}/experiments",
            "methods": ["GET"],
            "expected_response": 403},
    }
    
    check_endpoints(endpoints_to_test, token_name, token)

def test_check_auth_auditor_logger_level():
    # IMPORTANT: Empty DB, so HTTP responses could be different as expected
    if not SECRET_KEY:
        pytest.skip("Skipping test because the server is not secured")
        
    token_name = "AUDITOR+LOGGER"
    token = AUDITOR_LOGGER_TOKEN
    
    endpoints_to_test = {
        "root": {
            "url": f"{BASE_URL}/",
            "methods": ["GET"],
            "expected_response": 200},
        "docs": {
            "url": f"{BASE_URL}/docs",
            "methods": ["GET"],
            "expected_response": 200},
        "health": {
            "url": f"{BASE_URL}/health",
            "methods": ["GET"],
            "expected_response": 200},
        "history": {
            "url": f"{BASE_URL}/history",
            "methods": ["GET"],
            "expected_response": 204},
        "log": {
            "url": f"{BASE_URL}/log",
            "methods": ["GET", "POST"],
            "expected_response": {"GET": 400, "POST": 422},
            "data": "invalid_ttl_data"},
        "graph": {
            "url": f"{BASE_URL}/graph",
            "methods": ["GET", "DELETE"],
            "expected_response": {"GET": 204, "DELETE": 403}},
        "query": {
            "url": f"{BASE_URL}/query",
            "methods": ["GET"], 
            "expected_response": 403},
        "experiments": {
            "url": f"{BASE_URL}/experiments",
            "methods": ["GET"],
            "expected_response": 204},
    }
    
    check_endpoints(endpoints_to_test, token_name, token)

def test_check_auth_all_roles_levels():
    # IMPORTANT: Empty DB, so HTTP responses could be different as expected
    if not SECRET_KEY:
        pytest.skip("Skipping test because the server is not secured")
        
    token_name = "ALL_ROLES"
    token = ALL_ROLES_TOKEN
    
    endpoints_to_test = {
        "root": {
            "url": f"{BASE_URL}/",
            "methods": ["GET"],
            "expected_response": 200},
        "docs": {
            "url": f"{BASE_URL}/docs",
            "methods": ["GET"],
            "expected_response": 200},
        "health": {
            "url": f"{BASE_URL}/health",
            "methods": ["GET"],
            "expected_response": 200},
        "history": {
            "url": f"{BASE_URL}/history",
            "methods": ["GET"],
            "expected_response": 204},
        "log": {
            "url": f"{BASE_URL}/log",
            "methods": ["GET", "POST"],
            "expected_response": {"GET": 400, "POST": 422},
            "data": "invalid_ttl_data"},
        "graph": {
            "url": f"{BASE_URL}/graph",
            "methods": ["GET", "DELETE"],
            "expected_response": {"GET": 204, "DELETE": 204}},
        "query": {
            "url": f"{BASE_URL}/query",
            "methods": ["GET"], 
            "expected_response": 501},
        "experiments": {
            "url": f"{BASE_URL}/experiments",
            "methods": ["GET"],
            "expected_response": 204},
    }
    
    check_endpoints(endpoints_to_test, token_name, token)
