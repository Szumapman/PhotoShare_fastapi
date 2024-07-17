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
from src.schemas.photos import (
    PhotoOut,
    PhotoIn,
    PhotoCreated,
    TransformIn,
    RatingIn,
    RatingOut,
)
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
    """
    This endpoint is used to get all or queried photos (paginated). Photos can be sorted by date or rating.

    :param query: query to search in description or tags (optional)
    :type query: str | None
    :param user_id: user id to filter by (optional)
    :type user_id: int | None
    :param sort_by: how to sort photos (optional)
    :type sort_by: str | None
    :param current_user: user who performed request
    :type current_user: UserDb
    :param photo_repo: repository to work with
    :type photo_repo: AbstractPhotoRepo
    :param skip: number of photos to skip
    :type skip: int
    :param limit: number of photos to get
    :type limit: int
    :return: list of photos
    :rtype: list[PhotoOut]
    :raise: HTTPException 502 bad gateway if sort_by is not valid
    """
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
    """
    This endpoint is used to upload new photo.

    :param photo_info: data of new photo to upload - description and tags (optional)
    :type photo_info: PhotoIn
    :param photo: photo file to upload
    :type photo: UploadFile
    :param current_user: user who performed request
    :type current_user: UserDb
    :param photo_storage_provider: storage provider to upload photo to it
    :type photo_storage_provider: AbstractPhotoStorageProvider
    :param photo_repo: repository to work with
    :type photo_repo: AbstractPhotoRepo
    :return: photo with confirmation of upload
    :rtype: PhotoCreated
    """
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
    """
    This endpoint is used to get photo by id.

    :param photo_id: id of photo to get
    :type photo_id: int
    :param current_user: user who performed request
    :type current_user: UserDb
    :param photo_repo: repository to work with
    :type photo_repo: AbstractPhotoRepo
    :return: photo
    :rtype: PhotoOut
    """
    photo = await photo_repo.get_photo_by_id(photo_id)
    return photo


@router.get("/{photo_id}/qr_code", response_class=StreamingResponse)
async def get_qr_code(
    photo_id: int,
    transform_id: int | None = Query(
        None,
        description="Photo transformation id to apply to get the qr code",
    ),
    current_user: UserDb = Depends(auth_service.get_current_user),
    photo_repo: AbstractPhotoRepo = Depends(get_photo_repository),
    qr_code_provider: AbstractQrCodeProvider = Depends(get_qr_code_provider),
):
    """
    This endpoint is used to get photo or one of it transformation qr code.

    :param photo_id: id of photo to get
    :type photo_id: int
    :param transform_id: transformation id to get qr code of (optional)
    :type transform_id: int | None
    :param current_user: user who performed request
    :type current_user: UserDb
    :param photo_repo: repository to work with
    :type photo_repo: AbstractPhotoRepo
    :param qr_code_provider: qr code provider to get qr code from it
    :type qr_code_provider: AbstractQrCodeProvider
    :return: qr code
    :rtype: StreamingResponse
    :raise: NotFoundError if no transformation found for given transformation id
    """
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
    """
    This endpoint is used to delete photo by id.

    :param photo_id: id of photo to delete
    :type photo_id: int
    :param current_user: user who performed request
    :type current_user: UserDb
    :param photo_repo: repository to work with
    :type photo_repo: AbstractPhotoRepo
    :param photo_storage_provider: photo storage provider to delete photo from it
    :type photo_storage_provider: AbstractPhotoStorageProvider
    :return: deleted photo
    :rtype: PhotoOut
    """
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
    """
    This endpoint is used to update photo by id.

    :param photo_id: id of photo to update
    :type photo_id: int
    :param photo_info: new data of photo to update
    :type photo_info: PhotoIn
    :param current_user: user who performed request
    :type current_user: UserDb
    :param photo_repo: repository to work with
    :type photo_repo: AbstractPhotoRepo
    :return: updated photo
    :rtype: PhotoOut
    """
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
    """
    This endpoint is used to transform photo by id.

    :param photo_id: id of photo to transform
    :type photo_id: int
    :param transform: transformation parameters to apply to photo
    :type transform: TransformIn
    :param current_user: user who performed request
    :type current_user: UserDb
    :param photo_storage_provider: photo storage provider to transform photo
    :type photo_storage_provider: AbstractPhotoStorageProvider
    :param photo_repo: repository to work with
    :type photo_repo: AbstractPhotoRepo
    :return: updated photo
    :rtype: PhotoOut
    :raise: ForbiddenError if user who performs request is not owner of photo
    """
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


@router.post("/{photo_id}/rate", response_model=RatingOut)
async def rate_photo(
    photo_id: int,
    rating_in: RatingIn,
    current_user: UserDb = Depends(auth_service.get_current_user),
    photo_repo: AbstractPhotoRepo = Depends(get_photo_repository),
):
    """
    This endpoint is used to rate or change previous photo rating.

    :param photo_id: id of photo to rate
    :type photo_id: int
    :param rating_in: rating to apply to photo
    :type rating_in: RatingIn
    :param current_user: user who performed request
    :type current_user: UserDb
    :param photo_repo: repository to work with
    :type photo_repo: AbstractPhotoRepo
    :return: updated photo
    :rtype: PhotoOut
    """
    rating = await photo_repo.rate_photo(photo_id, rating_in, current_user.id)
    return RatingOut.model_validate(rating)
