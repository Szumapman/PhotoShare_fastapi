"""
Set of constants used in the project.
"""

from fastapi_limiter.depends import RateLimiter


MAX_DESCRIPTION_LENGTH = 1000
MAX_TAG_NAME_LENGTH = 50
MAX_COMMENT_LENGTH = 1000
MAX_USERNAME_LENGTH = 255
TOO_LONG_USERNAME_MESSAGE = (
    f"Username must be less than {MAX_USERNAME_LENGTH} characters long."
)
MIN_USERNAME_LENGTH = 3
TOO_SHORT_USERNAME_MESSAGE = (
    f"Username must be at least {MIN_USERNAME_LENGTH} characters long."
)
MAX_TAGS_AMOUNT = 5

MAX_PASSWORD_LENGTH = 45
TOO_LONG_PASSWORD_MESSAGE = (
    f"Password must be less than {MAX_PASSWORD_LENGTH} characters long."
)
MIN_PASSWORD_LENGTH = 8
TOO_SHORT_PASSWORD_MESSAGE = (
    f"Password must be at least {MIN_PASSWORD_LENGTH} characters long."
)
PASSWORD_PATTERN = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*\W).{8,45}$"
INVALID_PASSWORD_MESSAGE = "Password must contain at least one uppercase and lowercase letter, one digit and one special character"


ROLE_ADMIN = "admin"
ROLE_MODERATOR = "moderator"
ROLE_STANDARD = "standard"

API_V1 = "/api/v1"
API = API_V1
AUTH = "/auth"
USERS = "/users"
PHOTOS = "/photos"
COMMENTS = "/comments"
TAGS = "/tags"

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
FORBIDDEN_FOR_NOT_OWNER = "Only the owner can perform this operation."
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
TAG_NOT_FOUND = "Tag not found"

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
PHOTO_CREATED = "Photo successfully created"
PHOTO_DELETED = "Photo deleted"
PHOTO_UPDATED = "Photo updated"
PHOTO_RATED = "Photo rated"
RATING_DELETED = "Rating deleted"

COMMENT_CREATED = "Comment created"
COMMENT_NOT_FOUND = "Comment not found"
COMMENT_UPDATED = "Comment updated"
COMMENT_DELETED = "Comment deleted"

TAG_CREATED = "Tag created"
TAG_ALREADY_EXISTS = "Tag already exists"
TAG_UPDATED = "Tag updated"
TAG_DELETED = "Tag deleted"
TAGS_GET_ENUM = ["asc", "desc"]

REQUEST_AMOUNT_LIMIT = 180
RATE_LIMIT_TIME_IN_SECONDS = 60
RATE_LIMITER = RateLimiter(
    times=REQUEST_AMOUNT_LIMIT, seconds=RATE_LIMIT_TIME_IN_SECONDS
)
RATE_LIMITER_INFO = f"It is rate limited to {REQUEST_AMOUNT_LIMIT} requests per {RATE_LIMIT_TIME_IN_SECONDS} seconds."
