from testing_utils import *

logger = logging.getLogger("test.segb.credentials")

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
