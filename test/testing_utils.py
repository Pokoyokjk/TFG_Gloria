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
logger = logging.getLogger("test.segb.utils")
logger.setLevel(getattr(logging, logging_level, logging.INFO))
logger.addHandler(file_handler)


logger.info("Starting tests for the SEGB server...")
logger.info("Logging level set to %s", logging_level)
logger.info(f"Using env_file: {ENV_FILE}")

logger.debug(f"For paths, checking working directory: {os.getcwd()}")
BASE_URL = CONFIG.get("BASE_URL", "http://127.0.0.1:5000")
TEST_DB_VOLUME = CONFIG.get("TEST_DB_VOLUME", "segb-db-test")

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
    
