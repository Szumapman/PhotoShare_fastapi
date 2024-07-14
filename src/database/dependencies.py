from src.database.db import get_db
from src.repository.abstract import AbstractUserRepo, AbstractPhotoRepo
from src.repository.users import PostgresUserRepo
from src.repository.photos import PostgresPhotoRepo
from src.services.abstract import (
    AbstractAvatarProvider,
    AbstractPhotoStorageProvider,
    AbstractQrCodeProvider,
)
from src.services.avatar import AvatarProviderGravatar
from src.services.abstract import AbstractPasswordHandler
from src.services.password import BcryptPasswordHandler
from src.services.photo_storage_provider import CloudinaryPhotoStorageProvider
from src.services.qr_code import QrCodeProvider


def get_password_handler() -> AbstractPasswordHandler:
    return BcryptPasswordHandler()


def get_avatar_provider() -> AbstractAvatarProvider:
    return AvatarProviderGravatar()


def get_qr_code_provider() -> AbstractQrCodeProvider:
    return QrCodeProvider()


def get_photo_storage_provider() -> AbstractPhotoStorageProvider:
    return CloudinaryPhotoStorageProvider()


def get_user_repository() -> AbstractUserRepo:
    return PostgresUserRepo(next(get_db()))


def get_photo_repository() -> AbstractPhotoRepo:
    return PostgresPhotoRepo(next(get_db()))
