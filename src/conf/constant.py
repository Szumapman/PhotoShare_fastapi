MAX_DESCRIPTION_LENGTH = 1000
MAX_TAG_NAME_LENGTH = 50
MAX_COMMENT_LENGTH = 1000
MAX_USERNAME_LENGTH = 255

ROLE_ADMIN = "admin"
ROLE_MODERATOR = "moderator"
ROLE_STANDARD = "standard"

API_V1 = "/api/v1"
API = API_V1
AUTH = "/auth"
USERS = "/users"

ACCESS_TOKEN = "access_token"
REFRESH_TOKEN = "refresh_token"

USER_CREATED = "User successfully created"
USER_LOGOUT = "User logged out"

INVALID_SCOPE = "Invalid scope"
COULD_NOT_VALIDATE_CREDENTIALS = "Could not validate credentials"
LOG_IN_AGAIN = "You need to log in again"

HTTP_401_UNAUTHORIZED_DETAILS = [
    INVALID_SCOPE,
    COULD_NOT_VALIDATE_CREDENTIALS,
    LOG_IN_AGAIN,
]

FORBIDDEN_OPERATION_ON_ADMIN_ACCOUNT = (
    "Only admin can perform operations on users with admin role."
)
FORBIDDEN_FOR_USER = "Only admin or moderator can perform this operation."
FORBIDDEN_FOR_USER_AND_MODERATOR = "Only admin can perform this operation."
BANNED_USER = "User is banned."

HTTP_403_FORBIDDEN_DETAILS = [
    FORBIDDEN_OPERATION_ON_ADMIN_ACCOUNT,
    FORBIDDEN_FOR_USER,
    FORBIDDEN_FOR_USER_AND_MODERATOR,
    BANNED_USER,
]


TOKEN_NOT_FOUND = "Token not found"
USER_NOT_FOUND = "User not found"

HTTP_404_NOT_FOUND_DETAILS = [TOKEN_NOT_FOUND, USER_NOT_FOUND]

TOKEN_DELETED = "Token deleted"

REDIS_EXPIRE = 60 * 15  # seconds
ACCESS_TOKEN_EXPIRE = 15  # minutes
REFRESH_TOKEN_EXPIRE = 7  # days
