from fastapi import APIRouter, HTTPException, status, Security, Depends
from fastapi.security import (
    OAuth2PasswordRequestForm,
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from src.repository.abstract import AbstractUser
from src.database.dependencies import get_user_repository
from src.services.auth import auth_service
from src.conf.constant import (
    AUTH,
    HTTP_401_UNAUTHORIZED_DETAILS,
    HTTP_404_NOT_FOUND_DETAILS,
)
from src.schemas.users import UserCreated, UserIn, UserDb, TokenModel
from src.services.pasword import get_password_hash, verify_password

router = APIRouter(prefix=AUTH, tags=["auth"])
security = HTTPBearer()


@router.post("/signup", response_model=UserCreated, status_code=status.HTTP_201_CREATED)
async def signup(user: UserIn, user_repo: AbstractUser = Depends(get_user_repository)):
    if await user_repo.get_user_by_email(user.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Account with this email already exists",
        )
    if await user_repo.get_user_by_username(user.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Account with this username already exists",
        )
    user.password = get_password_hash(user.password)
    user = await user_repo.create_user(user)
    return UserCreated(user=UserDb.from_orm(user))


@router.post("/login", response_model=TokenModel)
async def login(
    body: OAuth2PasswordRequestForm = Depends(),
    user_repo: AbstractUser = Depends(get_user_repository),
):
    user = await user_repo.get_user_by_email(body.username)
    # because of security reasons we don't want to tell the user if the email or password is incorrect
    if user is None:
        # incorrect email
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    if not verify_password(body.password, user.password):
        # incorrect password
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    access_token, session_id = await auth_service.create_access_token(
        data={"sub": user.email}
    )
    refresh_token, expiration_date = await auth_service.create_refresh_token(
        data={"sub": user.email, "session_id": session_id}
    )
    await user_repo.add_refresh_token(user, refresh_token, expiration_date, session_id)
    return TokenModel(access_token=access_token, refresh_token=refresh_token)


@router.get("/refresh_token", response_model=TokenModel)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_repo: AbstractUser = Depends(get_user_repository),
):
    old_refresh_token = credentials.credentials
    answer = await auth_service.decode_refresh_token(old_refresh_token)
    if answer in HTTP_401_UNAUTHORIZED_DETAILS:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=answer)
    email = answer
    answer = await user_repo.get_user_by_email(email)
    if answer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account connected with this token does not found",
        )
    user = answer
    answer = await user_repo.delete_refresh_token(old_refresh_token, user.id)
    if answer in HTTP_404_NOT_FOUND_DETAILS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=answer)
    access_token, session_id = await auth_service.create_access_token(
        data={"sub": user.email}
    )
    refresh_token, expiration_date = await auth_service.create_refresh_token(
        data={"sub": user.email, "session_id": session_id}
    )
    await user_repo.add_refresh_token(user, refresh_token, expiration_date, session_id)
    return TokenModel(access_token=access_token, refresh_token=refresh_token)
