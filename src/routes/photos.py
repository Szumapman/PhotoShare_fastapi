from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    HTTPException,
    status,
    Query,
)

from src.conf.errors import ForbiddenError
from src.schemas.users import UserDb
from src.schemas.photos import PhotoOut, PhotoIn, PhotoCreated, TransformIn
from src.services.auth import auth_service
from src.repository.abstract import AbstractPhotoRepo
from src.services.abstract import AbstractPhotoStorageProvider
from src.database.dependencies import get_photo_repository
from src.database.dependencies import get_photo_storage_provider
from src.conf.constant import (
    PHOTOS,
    PHOTO_SEARCH_ENUMS,
    FORBIDDEN_FOR_NOT_OWNER,
)

router = APIRouter(prefix=PHOTOS, tags=["photos"])


@router.get("/", response_model=list[PhotoOut])
async def get_photos(
    query: str | None = Query(
        None, description="Search by keywords in description or tags"
    ),
    user_id: int | None = None,
    sort_by: str | None = Query(
        None,
        enum=PHOTO_SEARCH_ENUMS,
        description="Sort by date or rating",
    ),
    current_user: UserDb = Depends(auth_service.get_current_user),
    photo_repo: AbstractPhotoRepo = Depends(get_photo_repository),
):
    if sort_by and sort_by not in PHOTO_SEARCH_ENUMS:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail="Invalid sort type"
        )
    photos = await photo_repo.get_photos(query, user_id, sort_by)
    return photos


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
    photo_url = await photo_storage_provider.upload_photo(photo)
    qr_code_url = await photo_storage_provider.create_qr_code(photo_url)
    uploaded_photo = await photo_repo.upload_photo(
        current_user.id, photo_info, photo_url, qr_code_url
    )
    return uploaded_photo


@router.get("/{photo_id}", response_model=PhotoOut)
async def get_photo(
    photo_id: int,
    current_user: UserDb = Depends(auth_service.get_current_user),
    photo_repo: AbstractPhotoRepo = Depends(get_photo_repository),
):
    photo = await photo_repo.get_photo_by_id(photo_id)
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
    photo = await photo_repo.delete_photo(photo_id, current_user.id)
    await photo_storage_provider.delete_photo(photo)
    return photo


@router.patch("/{photo_id}", response_model=PhotoOut)
async def update_photo(
    photo_id: int,
    photo_info: PhotoIn,
    current_user: UserDb = Depends(auth_service.get_current_user),
    photo_repo: AbstractPhotoRepo = Depends(get_photo_repository),
):
    photo = await photo_repo.update_photo(photo_id, photo_info, current_user.id)
    return photo


@router.post("/{photo_id}/transform", response_model=PhotoOut)
async def transform_photo(
    photo_id: int,
    transform: TransformIn,
    current_user: UserDb = Depends(auth_service.get_current_user),
    photo_storage_provider: AbstractPhotoStorageProvider = Depends(
        get_photo_storage_provider
    ),
    photo_repo: AbstractPhotoRepo = Depends(get_photo_repository),
):
    photo = await photo_repo.get_photo_by_id(photo_id)
    if photo.user_id != current_user.id:
        raise ForbiddenError(detail=FORBIDDEN_FOR_NOT_OWNER)
    transform_url, transform_params = await photo_storage_provider.transform_photo(
        photo, transform
    )
    photo = await photo_repo.add_transform_photo(
        photo_id, transform_params, transform_url
    )
    return photo
