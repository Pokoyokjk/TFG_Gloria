from enum import Enum
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
import logging
import os

from pydantic import BaseModel

# Set up logging
logging_level = os.getenv("LOGGING_LEVEL", "INFO").upper()
log_file = os.getenv("SERVER_LOG_FILE", "segb_server.log")
# Ensure the logs directory exists
os.makedirs('/logs', exist_ok=True)
file_handler = logging.FileHandler(
    filename=f'/logs/{log_file}',
    mode='a',
    encoding='utf-8'
)
file_handler.setFormatter(logging.Formatter(
    fmt='%(asctime)s - %(name)s - %(levelname)s -> %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
))
logger = logging.getLogger("segb_server.utils.credentials")
logger.setLevel(getattr(logging, logging_level, logging.INFO))
logger.addHandler(file_handler)

logger.info("Starting SEGB server...")
logger.info("Logging level set to %s", logging_level)

SECRET_KEY = os.getenv("SECRET_KEY", None)
ALGORITHM = "HS256"

class Role(Enum):
    READER = "reader"
    LOGGER = "logger"
    ADMIN = "admin"

ROLES = [role.value for role in Role]

if not SECRET_KEY:
    logger.warning(
        "SECRET_KEY is not set. No security is enabled, and all reader endpoints are accessible without token validation.")
else:
    logger.info("Security via bearer token is enabled for endpoints.")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="./")
### TOKEN VALIDATION FUNCTIONS ###

class User(BaseModel):
    username: str
    name: str | None = None
    roles: list[str]
    exp: int

async def validate_token(token: Annotated[str, Depends(oauth2_scheme)]) -> dict:
    '''
        Validate the token for all endpoints.
        If the token is valid, return the decoded token data.
        If the token is invalid, return a 401 Unauthorized error.
        If the token is expired, return a 401 Unauthorized error.
        If no secret key is configured, return a default user object.
        In this case, security is disabled, and full access is granted ignoring the token.
        '''
    if SECRET_KEY is None:
        logger.warning(
            "SECRET_KEY is not set. No security is enabled, and all endpoints are accessible without token validation.")
        # If the secret is None, we assume no security is enabled
        return User(
            username="anonymous_reader",
            name="Unknown Reader - No Security Enabled",
            roles= [role for role in ROLES],
            exp=None
        )
    decode = None
    try:
        decode = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logger.info("Token validated successfully as READER Token")
        logger.debug(f"Decoded token data: {decode}")
        return User(**decode)
    except jwt.ExpiredSignatureError as e:
        logger.warning("Token has expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials. Expired Reader Token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.InvalidTokenError:
        logger.debug("Invalid Reader Token, trying to decode as Admin Token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials. Invalid Reader Token",
            headers={"WWW-Authenticate": "Bearer"}
        )

### END OF TOKEN VALIDATION FUNCTIONS ###