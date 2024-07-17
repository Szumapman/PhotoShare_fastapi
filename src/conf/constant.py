"""
Set of constants used in the project.
"""

MAX_DESCRIPTION_LENGTH = 1000
MAX_TAG_NAME_LENGTH = 50
MAX_COMMENT_LENGTH = 1000
MAX_USERNAME_LENGTH = 255
MAX_TAGS_AMOUNT = 5

ROLE_ADMIN = "admin"
ROLE_MODERATOR = "moderator"
ROLE_STANDARD = "standard"

API_V1 = "/api/v1"
API = API_V1
AUTH = "/auth"
USERS = "/users"
PHOTOS = "/photos"

ACCESS_TOKEN = "access_token"
REFRESH_TOKEN = "refresh_token"

USER_CREATED = "User successfully created"
USER_LOGOUT = "User logged out"
USER_UPDATE = "User updated"
USER_DELETE = "User deleted"

INVALID_SCOPE = "Invalid scope"
COULD_NOT_VALIDATE_CREDENTIALS = "Could not validate credentials"
LOG_IN_AGAIN = "You need to log in again"
INCORRECT_USERNAME_OR_PASSWORD = "Incorrect username or password"

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
FORBIDDEN_FOR_NOT_OWNER_AND_MODERATOR = (
    "Only owner or admin can perform this operation."
)
FORBIDDEN_FOR_NOT_OWNER = "Only the owner of the picture can perform this operation."
FORBIDDEN_FOR_OWNER = "Only not-owner can perform this operation."
BANNED_USER = "User is banned."

HTTP_403_FORBIDDEN_DETAILS = [
    FORBIDDEN_OPERATION_ON_ADMIN_ACCOUNT,
    FORBIDDEN_FOR_USER,
    FORBIDDEN_FOR_USER_AND_MODERATOR,
    FORBIDDEN_FOR_NOT_OWNER,
    BANNED_USER,
]


TOKEN_NOT_FOUND = "Token not found"
USER_NOT_FOUND = "User not found"
PHOTO_NOT_FOUND = "Photo not found"
RATING_NOT_FOUND = "Rating not found"

HTTP_404_NOT_FOUND_DETAILS = [TOKEN_NOT_FOUND, USER_NOT_FOUND, PHOTO_NOT_FOUND]

USERNAME_EXISTS = "User with this username already exists"
EMAIL_EXISTS = "User with this email already exists"

TOKEN_DELETED = "Token deleted"

REDIS_EXPIRE = 60 * 15  # seconds
ACCESS_TOKEN_EXPIRE = 15  # minutes
REFRESH_TOKEN_EXPIRE = 7  # days

AVATAR_WIDTH = 250
AVATAR_HEIGHT = 250
DEFAULT_AVATAR_URL_START_V1_GRAVATAR = "https://www.gravatar.com/avatar/"
CLOUDINARY_PHOTO_PUBLIC_ID_PREFIX = "PhotoShare_fastapi"
CLOUDINARY_AVATAR_PUBLIC_ID_PREFIX = CLOUDINARY_PHOTO_PUBLIC_ID_PREFIX + "/avatars"

PHOTO_SEARCH_ENUMS = [
    "upload_date-desc",
    "upload_date-asc",
    "rating-desc",
    "rating-asc",
]
INVALID_SORT_TYPE = "Invalid sort type"

RATING_DELETED = "Rating deleted"
