from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    HTTPException,
    status,
)

from src.schemas.users import UserDb
from src.schemas.photos import PhotoOut, PhotoIn, PhotoCreated
from src.services.auth import auth_service
from src.repository.abstract import AbstractPhotoRepo
from src.services.abstract import AbstractPhotoStorageProvider
from src.database.dependencies import get_photo_repository
from src.database.dependencies import get_photo_storage_provider
from src.routes.auth import is_current_user_logged_in
from src.conf.errors import PhotoStorageProviderError
from src.conf.constant import (
    PHOTOS,
    HTTP_404_NOT_FOUND_DETAILS,
    FORBIDDEN_FOR_NOT_OWNER_AND_MODERATOR,
)

router = APIRouter(prefix=PHOTOS, tags=["photos"])


@router.post("/", response_model=PhotoCreated, status_code=status.HTTP_201_CREATED)
async def create_photo(
    photo_info: PhotoIn,
    photo: UploadFile = File(),
    current_user: UserDb = Depends(auth_service.get_current_user),
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


@router.get("/{photo_id}", response_model=PhotoOut)
async def get_photo(
    photo_id: int,
    current_user: UserDb = Depends(auth_service.get_current_user),
    photo_repo: AbstractPhotoRepo = Depends(get_photo_repository),
):
    if await is_current_user_logged_in(current_user):
        photo = await photo_repo.get_photo_by_id(photo_id)
        print(photo)
        if photo in HTTP_404_NOT_FOUND_DETAILS:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=photo,
            )
        return photo


@router.delete("/{photo_id}", response_model=PhotoOut)
async def delete_photo(
    photo_id: int,
    current_user: UserDb = Depends(auth_service.get_current_user),
    photo_repo: AbstractPhotoRepo = Depends(get_photo_repository),
    photo_storage_provider: AbstractPhotoStorageProvider = Depends(
        get_photo_storage_provider
    ),
):
    if await is_current_user_logged_in(current_user):
        photo = await photo_repo.delete_photo(photo_id, current_user.id)
        if photo in HTTP_404_NOT_FOUND_DETAILS:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=photo,
            )
        if photo == FORBIDDEN_FOR_NOT_OWNER_AND_MODERATOR:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=photo,
            )
        try:
            await photo_storage_provider.delete_photo(photo)
        except PhotoStorageProviderError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Photo storage provider error: " + str(e),
            )
        return photo
