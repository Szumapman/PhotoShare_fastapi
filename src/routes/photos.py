from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    HTTPException,
    status,
    Query,
)
from fastapi.responses import StreamingResponse

from src.conf.errors import ForbiddenError, NotFoundError
from src.schemas.users import UserDb
from src.schemas.photos import PhotoOut, PhotoIn, PhotoCreated, TransformIn
from src.services.auth import auth_service
from src.repository.abstract import AbstractPhotoRepo
from src.services.abstract import AbstractPhotoStorageProvider, AbstractQrCodeProvider
from src.database.dependencies import (
    get_photo_repository,
    get_photo_storage_provider,
    get_qr_code_provider,
)
from src.conf.constant import (
    PHOTOS,
    PHOTO_SEARCH_ENUMS,
    FORBIDDEN_FOR_NOT_OWNER,
    INVALID_SORT_TYPE,
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
    skip: int = 0,
    limit: int = 10,
):
    if sort_by and sort_by not in PHOTO_SEARCH_ENUMS:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=INVALID_SORT_TYPE
        )
    photos = await photo_repo.get_photos(skip, limit, query, user_id, sort_by)
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
    uploaded_photo = await photo_repo.upload_photo(
        current_user.id,
        photo_info,
        photo_url,
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


@router.get("/{photo_id}/qr_code", response_class=StreamingResponse)
async def get_qr_code(
    photo_id: int,
    transform_id: int | None = Query(
        None,
        description="Transform id to apply to the qr code",
    ),
    current_user: UserDb = Depends(auth_service.get_current_user),
    photo_repo: AbstractPhotoRepo = Depends(get_photo_repository),
    qr_code_provider: AbstractQrCodeProvider = Depends(get_qr_code_provider),
):
    photo = await photo_repo.get_photo_by_id(photo_id)
    if transform_id:
        try:
            photo_url = photo.transformations[str(transform_id)][0]
        except KeyError:
            raise NotFoundError(
                detail=f"No data found for transformation id: {transform_id}"
            )
    else:
        photo_url = photo.photo_url
    return await qr_code_provider.stream_qr_code(photo_url)


@router.delete("/{photo_id}", response_model=PhotoOut)
async def delete_photo(
    photo_id: int,
    current_user: UserDb = Depends(auth_service.get_current_user),
    photo_repo: AbstractPhotoRepo = Depends(get_photo_repository),
    photo_storage_provider: AbstractPhotoStorageProvider = Depends(
        get_photo_storage_provider
    ),
):
    photo = await photo_repo.delete_photo(photo_id, current_user.id, current_user.role)
    await photo_storage_provider.delete_photo(photo.photo_url)
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
        photo.photo_url, transform
    )
    photo = await photo_repo.add_transform_photo(
        photo_id, transform_params, transform_url
    )
    return photo
