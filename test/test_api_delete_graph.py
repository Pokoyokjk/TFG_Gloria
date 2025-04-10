from testing_utils import *

logger = logging.getLogger("test.segb.api.graph.delete")

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
