from testing_utils import *

logger = logging.getLogger("test.segb.api.log.post")

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
