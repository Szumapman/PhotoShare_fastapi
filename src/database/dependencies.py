"""
This module contains all the dependencies for the application.
"""

from src.database.db import get_db
from src.repository.abstract import (
    AbstractUserRepo,
    AbstractPhotoRepo,
    AbstractCommentRepo,
    AbstractTagRepo,
)
from src.repository.comments import PostgresCommentRepo
from src.repository.tags import PostgresTagRepo
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
    """
    Function to get password handler.

    :return: password handler inherited from AbstractPasswordHandler
    """
    return BcryptPasswordHandler()


def get_avatar_provider() -> AbstractAvatarProvider:
    """
    Function to get avatar provider.

    :return: avatar provider inherited from AbstractAvatarProvider
    """
    return AvatarProviderGravatar()


def get_qr_code_provider() -> AbstractQrCodeProvider:
    """
    Function to get qr code provider.

    :return: qr code provider inherited from AbstractQrCodeProvider
    """
    return QrCodeProvider()


def get_photo_storage_provider() -> AbstractPhotoStorageProvider:
    """
    Function to get photo storage provider.

    :return: photo storage provider inherited from AbstractPhotoStorageProvider
    """
    return CloudinaryPhotoStorageProvider()


def get_user_repository() -> AbstractUserRepo:
    """
    Function to get user repository.

    :return: user repository inherited from AbstractUserRepo
    """
    return PostgresUserRepo(next(get_db()))


def get_photo_repository() -> AbstractPhotoRepo:
    """
    Function to get photo repository.

    :return: photo repository inherited from AbstractPhotoRepo
    """
    return PostgresPhotoRepo(next(get_db()))


def get_comment_repository() -> AbstractCommentRepo:
    """
    Function to get comment repository.

    :return: comment repository inherited from AbstractCommentRepo
    """
    return PostgresCommentRepo(next(get_db()))


def get_tag_repository() -> AbstractTagRepo:
    """
    Function to get tag repository.
    """
    return PostgresTagRepo(next(get_db()))
