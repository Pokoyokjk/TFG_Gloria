
import jwt
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from utils.credentials import Role

# Load environment variables from a .env file
load_dotenv()
# This must be generated with the command:
# openssl rand -hex 32
SECRET_KEY = os.getenv("SECRET_KEY", None)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_WEEKS = 50

expire = datetime.now(timezone.utc) + timedelta(weeks=ACCESS_TOKEN_EXPIRE_WEEKS)

# Generate tokens for different users

# Reader token
reader_user = {
    "username": "reader_user",
    "name": "Reader User Name",
    "roles": [Role.READER.value],
    "exp": expire
}

# Logger and Reader token
reader_token = jwt.encode(reader_user, SECRET_KEY, algorithm=ALGORITHM)
print("Reader Token:", reader_token)

logger_user = {
    "username": "logger_user",
    "name": "Logger User Name",
    "roles": [Role.LOGGER.value],
    "exp": expire
}
logger_token = jwt.encode(logger_user, SECRET_KEY, algorithm=ALGORITHM)
print("Logger Token:", logger_token)

reader_logger_user = {
    "username": "reader_logger_user",
    "name": "Reader Logger User Name",
    "roles": [Role.READER.value, Role.LOGGER.value],
    "exp": expire
}
reader_logger_token = jwt.encode(reader_logger_user, SECRET_KEY, algorithm=ALGORITHM)
print("Reader/Logger Token:", reader_logger_token)

# Admin token
admin_user = {
    "username": "admin_user",
    "name": "Admin User Name",
    "roles": [Role.ADMIN.value],
    "exp": expire
}
admin_token = jwt.encode(admin_user, SECRET_KEY, algorithm=ALGORITHM)
print("Admin Token:", admin_token)

# or... (equivalent to above)
all_roles_user = {
    "username": "full_admin_user",
    "name": "Full Admin User Name",
    "roles": [role.value for role in Role],
    "exp": expire
}
all_roles_token = jwt.encode(all_roles_user, SECRET_KEY, algorithm=ALGORITHM)
print("Full Admin Token:", all_roles_token)