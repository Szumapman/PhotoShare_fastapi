from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    Form,
    HTTPException,
    status,
    Query,
)

from src.database.models import User
from src.schemas.photos import PhotoOut, PhotoIn, PhotoCreated
from src.services.auth import auth_service
from src.repository.abstract import AbstractPhotoRepo
from src.services.abstract import AbstractPhotoStorageProvider
from src.database.dependencies import get_photo_repository
from src.database.dependencies import get_photo_storage_provider
from src.routes.auth import is_current_user_logged_in
from src.conf.errors import PhotoStorageProviderError


router = APIRouter(prefix="/photos", tags=["photos"])


@router.post("/", response_model=PhotoCreated, status_code=status.HTTP_201_CREATED)
async def create_photo(
    photo_info: PhotoIn,
    photo: UploadFile = File(),
    current_user: User = Depends(auth_service.get_current_user),
    photo_storage_provider: AbstractPhotoStorageProvider = Depends(
        get_photo_storage_provider
    ),
    photo_repo: AbstractPhotoRepo = Depends(get_photo_repository),
):
    try:
        if await is_current_user_logged_in(current_user):
            photo_url = await photo_storage_provider.upload_photo(photo)
            qr_code_url = await photo_storage_provider.create_qr_code(photo_url)
            uploaded_photo = await photo_repo.upload_photo(
                current_user.id, photo_info, photo_url, qr_code_url
            )
            return uploaded_photo
    except PhotoStorageProviderError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Photo storage provider error: " + str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
