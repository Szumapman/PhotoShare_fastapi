from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi_limiter import FastAPILimiter
from redis.asyncio import Redis

from src.conf.config import settings
from src.routes import auth, users, photos, comments, tags
from src.conf.constants import API
from src.conf.errors import (
    NotFoundError,
    ForbiddenError,
    UnauthorizedError,
    PhotoStorageProviderError,
    ConflictError,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    Initialize FastAPI Limiter on app startup, to prevent abuse and ensure fair usage of the API.

    :param _: FastAPI app instance
    :type _: FastAPI
    """
    redis_connection = await Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        password=settings.redis_password,
        db=0,
        encoding="utf-8",
        decode_responses=True,
    )
    await FastAPILimiter.init(
        redis_connection,
    )
    yield
    await FastAPILimiter.close()


app = FastAPI(lifespan=lifespan)

origins = ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=API)
app.include_router(users.router, prefix=API)
app.include_router(photos.router, prefix=API)
app.include_router(comments.router, prefix=API)
app.include_router(tags.router, prefix=API)


@app.exception_handler(NotFoundError)
async def not_found_exception_handler(request, exc):
    """
    Raise a 404 error when a requested resource is not found.

    :param request: request object
    :type request: Request
    :param exc: exception object
    :type exc: NotFoundError
    :raise HTTPException: 404 not found error
    """
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail)


@app.exception_handler(ForbiddenError)
async def forbidden_exception_handler(request, exc):
    """
    Raise a 403 error when a user has no permission to do the requested action.

    :param request: request object
    :type request: Request
    :param exc: exception object
    :type exc: ForbiddenError
    :raise HTTPException: 403 forbidden error
    """
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.detail)


@app.exception_handler(UnauthorizedError)
async def unauthorized_exception_handler(request, exc):
    """
    Raise a 401 error when a user is not authorized to access a resource.

    :param request: request object
    :type request: Request
    :param exc: exception object
    :type exc: UnauthorizedError
    :raise HTTPException: 401 unauthorized error
    """
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.detail)


@app.exception_handler(ConflictError)
async def conflict_exception_handler(request, exc):
    """
    Raise a 409 error when you try to create a resource that already exists and must be unique.

    :param request: request object
    :type request: Request
    :param exc: exception object
    :type exc: ConflictError
    :raise HTTPException: 409 conflict error
    """
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.detail)


@app.exception_handler(PhotoStorageProviderError)
async def photo_storage_provider_exception_handler(request, exc):
    """
    Raise a 502 error when a photo storage provider is not available.

    :param request: request object
    :type request: Request
    :param exc: exception object
    :type exc: PhotoStorageProviderError
    :raise HTTPException: 502 bad gateway error
    """
    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=exc.detail)


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
