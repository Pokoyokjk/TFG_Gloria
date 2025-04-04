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
logger = logging.getLogger("segb_server.credentials_utils")
logger.setLevel(getattr(logging, logging_level, logging.INFO))
logger.addHandler(file_handler)

logger.info("Starting SEGB server...")
logger.info("Logging level set to %s", logging_level)


SECRET_KEY_READERS = os.getenv("SECRET_KEY_READERS", None)
SECRET_KEY_LOGGERS = os.getenv("SECRET_KEY_LOGGERS", None)
SECRET_KEY_ADMINS = os.getenv("SECRET_KEY_ADMINS", None)
ALGORITHM = "HS256"

if not SECRET_KEY_READERS:
    logger.warning(
        "SECRET_KEY_READERS is not set. No security is enabled, and all reader endpoints are accessible without token validation.")
else:
    logger.info("Security via bearer token is enabled for reader endpoints.")
if not SECRET_KEY_LOGGERS:
    logger.warning(
        "SECRET_KEY_LOGGERS is not set. No security is enabled, and all logger endpoints are accessible without token validation.")
else:
    logger.info("Security via bearer token is enabled for logger endpoints.")
if not SECRET_KEY_ADMINS:
    logger.warning(
        "SECRET_KEY_ADMINS is not set. No security is enabled, and all admin endpoints are accessible without token validation.")
else:
    logger.info("Security via bearer token is enabled for admin endpoints.")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="./")
### TOKEN VALIDATION FUNCTIONS ###

class User(BaseModel):
    username: str
    name: str | None = None
    exp: int | None = None

# Define a function for readers endpoints
async def validate_token_for_readers_endpoint(token: Annotated[str, Depends(oauth2_scheme)]) -> dict:
    '''
        Validate the token for reader endpoints.
        Only readers have access to these endpoints.
        If the token is valid, return the decoded token data.
        If the token is invalid, return a 401 Unauthorized error.
        If the token is expired, return a 401 Unauthorized error.
        If no readers secret key is configured, return a default user object.
        In this case, security is disabled, and full access is granted ignoring the token.
        '''
    if SECRET_KEY_READERS is None:
        logger.warning(
            "SECRET_KEY_READERS is not set. No security is enabled, and all reader endpoints are accessible without token validation.")
        # If the secret is None, we assume no security is enabled
        return User(
            username="anonymous_reader",
            name="Unknown Reader - No Security Enabled",
            exp=None
        )
    decode = None
    try:
        decode = validate_token(token, SECRET_KEY_READERS)
    except jwt.ExpiredSignatureError as e:
        logger.warning("Token has expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials. Expired Reader Token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.InvalidTokenError:
        logger.debug("Invalid Reader Token, trying to decode as Admin Token")
        # If the token is invalid as a user token, attempt to decode it as an admin token.
        # This allows admin tokens to access user endpoints, but user tokens cannot access admin endpoints.
        try:
            decode = validate_token(token, SECRET_KEY_ADMINS)
        except jwt.InvalidTokenError as e:
            try:
                validate_token(token, SECRET_KEY_LOGGERS)
                logger.warning("Logger token used for Reader endpoint")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access forbidden: Logger tokens cannot access Reader endpoints",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            except jwt.InvalidTokenError:
                pass  # Not a Logger token, continue checking
            
            logger.warning("Invalid Reader Token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials. Invalid Reader Token",
                headers={"WWW-Authenticate": "Bearer"}
            )
    logger.info("Token validated successfully as READER Token")
    logger.debug(f"Decoded token data: {decode}")
    return User(**decode)

# Define a function for loggers endpoints
async def validate_token_for_loggers_endpoint(token: Annotated[str, Depends(oauth2_scheme)]) -> dict:
    '''
        Validate the token for logger endpoints.
        Only loggers have access to these endpoints.
        If the token is valid, return the decoded token data.
        If the token is invalid, return a 401 Unauthorized error.
        If the token is expired, return a 401 Unauthorized error.
        If no loggers secret key is configured, return a default user object.
        In this case, security is disabled, and full access is granted ignoring the token.
        '''
    if SECRET_KEY_LOGGERS is None:
        logger.warning(
            "SECRET_KEY_LOGGERS is not set. No security is enabled, and all logger endpoints are accessible without token validation.")
        # If the secret is None, we assume no security is enabled
        return User(
            username="anonymous_logger",
            name="Unknown Logger - No Security Enabled",
            exp=None
        )
    decode = None
    try:
        decode = validate_token(token, SECRET_KEY_LOGGERS)
    except jwt.ExpiredSignatureError as e:
        logger.warning("Token has expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials. Expired Logger Token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.InvalidTokenError:
        logger.debug("Invalid Logger Token, trying to decode as Admin or Reader Token")
        # If the token is invalid as a user token, attempt to decode it as an admin token.
        # This allows admin tokens to access user endpoints, but user tokens cannot access admin endpoints.
        try:
            decode = validate_token(token, SECRET_KEY_ADMINS)
        except jwt.InvalidTokenError:
            logger.debug("Invalid Logger Token, trying to decode as Reader Token for 403 Forbidden")
            # Check if the token is valid as a Reader
            try:
                validate_token(token, SECRET_KEY_READERS)
                logger.warning("Reader token used for Logger endpoint")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access forbidden: Reader tokens cannot access Logger endpoints",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            except jwt.InvalidTokenError:
                pass  # Not a Reader token, continue checking

            logger.warning("Invalid Logger Token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials. Invalid Logger Token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        logger.info("Token validated successfully as LOGGER Token")
    logger.debug(f"Decoded token data: {decode}")
    return User(**decode)

# Define a function for admin endpoints
async def validate_token_for_admin_endpoint(token: Annotated[str, Depends(oauth2_scheme)]) -> dict:
    '''
        Validate the token for admin endpoints.
        Only admins have access to these endpoints.
        If the token is valid, return the decoded token data.
        If the token is invalid, return a 401 Unauthorized error.
        If the token is expired, return a 401 Unauthorized error.
        If no admins secret key is configured, return a default user object.
        In this case, security is disabled, and full access is granted ignoring the token.
        '''
    if SECRET_KEY_ADMINS is None:
        logger.warning(
            "SECRET_KEY_ADMINS is not set. No security is enabled, and all admin endpoints are accessible without token validation.")
        # If the secret is None, we assume no security is enabled
        return User(
            username="anonymous_admin",
            name="Unknown Admin - No Security Enabled",
            exp=None
        )
    decode = None
    try:
        decode = validate_token(token, SECRET_KEY_ADMINS)
    except jwt.ExpiredSignatureError as e:
        logger.warning("Token has expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials. Expired Admin Token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.InvalidTokenError:
        logger.debug("Invalid admin token, trying to decode as Reader or Logger Token for 403 Forbidden")
        # Check if the token is valid as a Reader or Logger
        try:
            validate_token(token, SECRET_KEY_READERS)
            logger.warning("Reader token used for Admin endpoint")
            raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Reader tokens cannot access Admin endpoints",
            headers={"WWW-Authenticate": "Bearer"}
            )
        except jwt.InvalidTokenError:
            pass  # Not a Reader token, continue checking

        try:
            validate_token(token, SECRET_KEY_LOGGERS)
            logger.warning("Logger token used for Admin endpoint")
            raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Logger tokens cannot access Admin endpoints",
            headers={"WWW-Authenticate": "Bearer"}
            )
        except jwt.InvalidTokenError:
            pass  # Not a Logger token, continue checking
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials. Invalid Admin Token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    logger.info("Token validated successfully as ADMIN Token")
    logger.debug(f"Decoded token data: {decode}")
    return User(**decode)

def validate_token(token: str, secret: str) -> dict:
    '''
    Validate the token using the secret key
    Decode the token and verify its signature
    If the token is valid, return the decoded token data
    If the token is invalid, raise an exception
    '''
    return jwt.decode(token, secret, algorithms=[ALGORITHM])
### END OF TOKEN VALIDATION FUNCTIONS ###