import uvicorn
from fastapi import FastAPI, HTTPException, status

from src.routes import auth, users, photos, comments
from src.conf.constant import API
from src.conf.errors import (
    NotFoundError,
    ForbiddenError,
    UnauthorizedError,
    PhotoStorageProviderError,
)


app = FastAPI()

app.include_router(auth.router, prefix=API)
app.include_router(users.router, prefix=API)
app.include_router(photos.router, prefix=API)
app.include_router(comments.router, prefix=API)


@app.exception_handler(NotFoundError)
async def not_found_exception_handler(request, exc):
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail)


@app.exception_handler(ForbiddenError)
async def forbidden_exception_handler(request, exc):
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.detail)


@app.exception_handler(UnauthorizedError)
async def unauthorized_exception_handler(request, exc):
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.detail)


@app.exception_handler(PhotoStorageProviderError)
async def photo_storage_provider_exception_handler(request, exc):
    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=exc.detail)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
