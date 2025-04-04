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
load_dotenv("test.env")

logging_level = os.getenv("LOGGING_LEVEL", "INFO").upper()
log_file = os.getenv("TESTS_LOG_FILE", "test_segb_server.log")
compose_file = os.getenv("COMPOSE_FILE", "compose_test.yaml")
# Ensure the logs directory exists
os.makedirs('./logs', exist_ok=True)
file_handler = logging.FileHandler(
    filename=f'./logs/{log_file}',
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
BASE_URL = "http://127.0.0.1:5000"  
TEST_DB_VOLUME = "amor-segb-db-test"

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
import csv

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
    
    assert response.status_code == 200, f"Expected HTTP 200 OK code, but got {response.status_code}"
    
    
    
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
        
    url = f"{BASE_URL}/graph"
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
    
    url = f"{BASE_URL}/graph"
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

    url = f"{BASE_URL}/graph"
    response = requests.get(url)

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
    headers = {"Content-Type": "text/turtle"}
    
    ttl_data = """
        @prefix ex: <http://example.org/> .
        ex:subject ex:predicate "object" .
    """
    response = requests.post(url, headers=headers, data=ttl_data)
    assert response.status_code == 200, f"Expected HTTP 200 OK code when inserting data, but got {response.status_code}"
    
    url = f"{BASE_URL}/graph"
    response = requests.delete(url)
    print(response.text)
    
    assert response.status_code == 200, f"Expected HTTP 200 OK code when deleting graph, but got {response.status_code}"
    
    url = f"{BASE_URL}/graph"
    response = requests.get(url)
    
    assert response.status_code == 204, f"Expected HTTP 204 Empty Content code, but got {response.status_code}"
    assert response.text == "", f"Expected empty response, but got {response.text}"

def test_DELETE_empty_graph():
    # Test the DELETE /graph endpoint when the graph is already empty
    
    # Ensure the graph is empty by attempting to delete it first
    url = f"{BASE_URL}/graph"
    response = requests.delete(url)
    assert response.status_code in [200, 204], f"Expected HTTP 200 or 204 when ensuring graph is empty, but got {response.status_code}"
    
    # Attempt to delete the graph again
    response = requests.delete(url)
    assert response.status_code == 204, f"Expected HTTP 204 No Content when deleting an already empty graph, but got {response.status_code}"
    assert response.text.strip() == "", f"Expected empty response body for 204, but got: {response.text}"

    
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
    
    # Test the get log endpoint
    url = f"{BASE_URL}/log?log_id={log_id}"
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
    # Test the get /log endpoint with no logs in the graph
    url = f"{BASE_URL}/log?log_id=nonexistent_id"
    response = requests.get(url)

    # Assert that the response status code is 404 (Log Info not found)
    assert response.status_code == 404, f"Expected HTTP 404 Not Found, but got {response.status_code}"
    assert response.json() == "Log Info not found", f"Expected 'Log Info not found', but got {response.json()}"

    # Test the get /log endpoint without providing log_id
    url = f"{BASE_URL}/log"
    response = requests.get(url)

    # Assert that the response status code is 400 (Missing log_id parameter)
    assert response.status_code == 400, f"Expected HTTP 400 Bad Request, but got {response.status_code}"
    assert response.json() == "Missing log_id parameter", f"Expected 'Missing log_id parameter', but got {response.json()}"
    
def test_GET_experiments_basic():
    # Test the /experiments endpoint
    
    # Insert a log entry to populate the SEGB
    url = f"{BASE_URL}/log"
    headers = {"Content-Type": "text/turtle"}
    
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
    assert response.status_code == 200, f"Expected HTTP 200 OK code when inserting log, but got {response.status_code}"
    
    url = f"{BASE_URL}/experiments"
    response = requests.get(url)
    assert response.status_code == 200, f"Expected HTTP 200 OK code, but got {response.status_code}"
    
    # Parse the response JSON and verify the experiment URIs
    resulting_uris = response.text.splitlines()
    expected_uris = [
        "experiment_uri",
        "http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#exp1",
        "http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#exp2",
        "http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#exp3",
        "http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#exp4",
    ]

    # Verify that all expected URIs are present in the response
    logger.debug(f"Experiment list: {resulting_uris}")
    logger.debug(f"Expected URIs: {expected_uris}")
    for uri in expected_uris:
        assert uri in resulting_uris, f"Expected URI {uri} is missing in the response"

    # Verify that there are no unexpected URIs in the response
    for uri in resulting_uris:
        assert uri in expected_uris, f"Unexpected URI {uri} found in the response"

def test_GET_experiments_extended():
    # Test the /experiments endpoint
    
    # Insert a log entry to populate the SEGB
    url = f"{BASE_URL}/log"
    headers = {"Content-Type": "text/turtle"}
    
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
    assert response.status_code == 200, f"Expected HTTP 200 OK code when inserting log, but got {response.status_code}"
    
    url = f"{BASE_URL}/experiments"
    response = requests.get(url)
    assert response.status_code == 200, f"Expected HTTP 200 OK code, but got {response.status_code}"
    
    # Parse the response JSON and verify the experiment URIs
    resulting_uris = response.text.splitlines()
    expected_uris = [
        "experiment_uri",
        "http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#exp1",
        "http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#exp2",
        "http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#exp3",
        "http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#exp4",
    ]

    # Verify that all expected URIs are present in the response
    logger.debug(f"Experiment list: {resulting_uris}")
    logger.debug(f"Expected URIs: {expected_uris}")
    for uri in expected_uris:
        assert uri in resulting_uris, f"Expected URI {uri} is missing in the response"

    # Verify that there are no unexpected URIs in the response
    for uri in resulting_uris:
        assert uri in expected_uris, f"Unexpected URI {uri} found in the response"

def test_GET_experiments_extended_several_logs():
    # Test the /experiments endpoint
    
    # Insert a log entry to populate the SEGB
    url = f"{BASE_URL}/log"
    headers = {"Content-Type": "text/turtle"}
    
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
    assert response.status_code == 200, f"Expected HTTP 200 OK code when inserting log, but got {response.status_code}"
    
    ttl_data = """
        @prefix amor-exp: <http://www.gsi.upm.es/ontologies/amor/experiments/ns#> .
        @prefix amor-exec: <http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#> .
        
        amor-exec:exp1 a amor-exp:Experiment .
        amor-exec:exp5 a amor-exp:Experiment .
        amor-exec:exp3 a amor-exp:Experiment .
        amor-exec:exp6 a amor-exp:Experiment .
    """
    response = requests.post(url, headers=headers, data=ttl_data)
    assert response.status_code == 200, f"Expected HTTP 200 OK code when inserting log, but got {response.status_code}"
    
    url = f"{BASE_URL}/experiments"
    response = requests.get(url)
    assert response.status_code == 200, f"Expected HTTP 200 OK code, but got {response.status_code}"
    
    # Parse the response JSON and verify the experiment URIs
    resulting_uris = response.text.splitlines()
    expected_uris = [
        "experiment_uri",
        "http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#exp1",
        "http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#exp2",
        "http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#exp3",
        "http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#exp4",
        "http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#exp5",
        "http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns#exp6",
    ]

    # Verify that all expected URIs are present in the response
    for uri in expected_uris:
        assert uri in resulting_uris, f"Expected URI {uri} is missing in the response"

    # Verify that there are no unexpected URIs in the response
    for uri in resulting_uris:
        assert uri in expected_uris, f"Unexpected URI {uri} found in the response"


def test_GET_experiments_without_logged_experiments():
    # Test the /experiments endpoint
    
    url = f"{BASE_URL}/experiments"
    response = requests.get(url)
    assert response.status_code == 200, f"Expected HTTP 200 OK code, but got {response.status_code}"
    
    # Parse the response JSON and verify the experiment URIs
    resulting_uris = response.text.splitlines()
    expected_uris = [
        "experiment_uri",
    ]

    # Verify that all expected URIs are present in the response
    for uri in expected_uris:
        assert uri in resulting_uris, f"Expected URI {uri} is missing in the response"

    # Verify that there are no unexpected URIs in the response
    for uri in resulting_uris:
        assert uri in expected_uris, f"Unexpected URI {uri} found in the response"

def test_GET_experiment():
    # Test the /experiment endpoint
    
    # Insert a log entry to populate the SEGB
    url = f"{BASE_URL}/log"
    headers = {"Content-Type": "text/turtle"}
    
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
    assert response.status_code == 200, f"Expected HTTP 200 OK code when inserting log, but got {response.status_code}"
    
    # Test the get experiment endpoint    
    url = f"{BASE_URL}/experiment?namespace=http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns&experiment_id=exp1"
    response = requests.get(url)
    
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
    
def test_GET_experiment_non_existing_experiment_uri():
    # Test the /experiment endpoint
    
    # Insert a log entry to populate the SEGB
    url = f"{BASE_URL}/log"
    headers = {"Content-Type": "text/turtle"}
    
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
    assert response.status_code == 200, f"Expected HTTP 200 OK code when inserting log, but got {response.status_code}"
    
    # Test the get experiment endpoint
    url = f"{BASE_URL}/experiment?namespace=http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns&experiment_id=exp10"
    response = requests.get(url)
    
    assert response.status_code == 404, f"Expected HTTP 404 Not Found, but got {response.status_code}"

def test_GET_experiment_missing_experiment():
    # Test the /experiment endpoint
    # Test the get experiment endpoint
    url = f"{BASE_URL}/experiment?namespace=http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns&experiment_id=exp1"
    response = requests.get(url)
    assert response.status_code == 404, f"Expected HTTP 404 Not Found, but got {response.status_code}"
    
def test_GET_experiment_missing_experiment_id():
    # Test the /experiment endpoint
    # Test the get experiment endpoint
    url = f"{BASE_URL}/experiment?namespace=http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns"
    response = requests.get(url)
    assert response.status_code == 422, f"Expected HTTP 422 Unprocessable Entity, but got {response.status_code}"

def test_GET_experiment_missing_namespace():
    # Test the /experiment endpoint
    # Test the get experiment endpoint
    url = f"{BASE_URL}/experiment?experiment_id=exp1"
    response = requests.get(url)
    assert response.status_code == 422, f"Expected HTTP 422 Unprocessable Entity, but got {response.status_code}"

def test_GET_experiment_missing_namespace_and_experiment_id():
    # Test the /experiment endpoint
    # Test the get experiment endpoint
    url = f"{BASE_URL}/experiment"
    response = requests.get(url)
    assert response.status_code == 422, f"Expected HTTP 422 Unprocessable Entity, but got {response.status_code}"

def test_GET_log_with_json_params():
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
    
    # Test the get log endpoint with JSON parameters
    url = f"{BASE_URL}/log"
    headers = {"Content-Type": "application/json"}
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
    headers = {"Content-Type": "text/turtle"}
    
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
    assert response.status_code == 200, f"Expected HTTP 200 OK code when inserting log, but got {response.status_code}"
    
    # Test the get experiment endpoint with JSON parameters
    url = f"{BASE_URL}/experiment"
    headers = {"Content-Type": "application/json"}
    json_data = {
        "namespace": "http://www.gsi.upm.es/ontologies/amor/experiments/execution/ns",
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

def test_GET_experiment_with_json_params_hashtag_namespace():
    # Insert a log entry to populate the SEGB
    url = f"{BASE_URL}/log"
    headers = {"Content-Type": "text/turtle"}
    
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
    assert response.status_code == 200, f"Expected HTTP 200 OK code when inserting log, but got {response.status_code}"
    
    # Test the get experiment endpoint with JSON parameters and namespace ending with a hashtag
    url = f"{BASE_URL}/experiment"
    headers = {"Content-Type": "application/json"}
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
    headers = {"Content-Type": "text/turtle"}
    
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
    assert response.status_code == 200, f"Expected HTTP 200 OK code when inserting log, but got {response.status_code}"
    
    # Test the get experiment endpoint with JSON parameters and namespace ending with a hashtag
    url = f"{BASE_URL}/experiment"
    headers = {"Content-Type": "application/json"}
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