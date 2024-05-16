from fastapi import APIRouter, HTTPException, status, Security, Depends
from fastapi.security import (
    OAuth2PasswordRequestForm,
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from src.repository.abstract import AbstractUserRepo
from src.database.dependencies import get_user_repository
from src.services.auth import auth_service
from src.conf.constant import (
    AUTH,
    HTTP_401_UNAUTHORIZED_DETAILS,
    HTTP_404_NOT_FOUND_DETAILS,
    USER_LOGOUT,
    USER_CREATED,
)
from src.schemas.users import UserInfo, UserIn, UserDb, TokenModel
from src.database.models import User
from src.services.pasword import get_password_hash, verify_password

router = APIRouter(prefix=AUTH, tags=["auth"])
security = HTTPBearer()


async def __is_current_user_logged_in(current_user) -> User:
    if current_user in HTTP_401_UNAUTHORIZED_DETAILS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=current_user
        )
    return current_user


async def __set_tokens(user: User, user_repo: AbstractUserRepo) -> TokenModel:
    access_token, session_id = await auth_service.create_access_token(
        data={"sub": user.email}
    )
    refresh_token, expiration_date = await auth_service.create_refresh_token(
        data={"sub": user.email, "session_id": session_id}
    )
    await user_repo.add_refresh_token(user, refresh_token, expiration_date, session_id)
    return TokenModel(access_token=access_token, refresh_token=refresh_token)


@router.post("/signup", response_model=UserInfo, status_code=status.HTTP_201_CREATED)
async def signup(
    user: UserIn, user_repo: AbstractUserRepo = Depends(get_user_repository)
):
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
    return UserInfo(user=UserDb.from_orm(user), detail=USER_CREATED)


@router.post("/login", response_model=TokenModel)
async def login(
    body: OAuth2PasswordRequestForm = Depends(),
    user_repo: AbstractUserRepo = Depends(get_user_repository),
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
    return await __set_tokens(user, user_repo)


@router.get("/refresh_token", response_model=TokenModel)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Security(security),
    user_repo: AbstractUserRepo = Depends(get_user_repository),
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
    return await __set_tokens(user, user_repo)


@router.post("/logout", response_model=UserInfo)
async def logout(
    current_user: User = Depends(auth_service.get_current_user),
    credentials: HTTPAuthorizationCredentials = Security(security),
    user_repo: AbstractUserRepo = Depends(get_user_repository),
):
    if await __is_current_user_logged_in(current_user):
        token = credentials.credentials
        answer = await auth_service.get_session_id_from_token(token, current_user.email)
        if answer in HTTP_401_UNAUTHORIZED_DETAILS:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=answer)
        session_id = answer
        answer = await user_repo.logout_user(token, session_id, current_user)
        if answer in HTTP_404_NOT_FOUND_DETAILS:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=answer)
        user = answer
        return UserInfo(user=UserDb.from_orm(user), detail=USER_LOGOUT)


@router.get("/secret")
async def read_secret(current_user: User = Depends(auth_service.get_current_user)):
    if await __is_current_user_logged_in(current_user):
        return {"message": "secret", "owner": current_user.email}
