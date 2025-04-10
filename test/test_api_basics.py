from testing_utils import *

logger = logging.getLogger("test.segb.basics")

def test_GET_healthcheck():
    
    response = requests.get(BASE_URL + "/health")
    assert response.status_code == 200, f"Expected HTTP 200 OK code, but got {response.status_code}"

def test_GET_root():
    response = requests.get(BASE_URL + "/")
    assert response.status_code == 200, f"Expected HTTP 200 OK code, but got {response.status_code}"

def test_GET_docs():
    response = requests.get(BASE_URL + "/docs")
    assert response.status_code == 200, f"Expected HTTP 200 OK code, but got {response.status_code}"