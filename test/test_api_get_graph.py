from testing_utils import *

logger = logging.getLogger("test.segb.api.graph.get")

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
