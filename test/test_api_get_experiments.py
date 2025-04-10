from testing_utils import *

logger = logging.getLogger("test.segb.api.experiments.get")

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
