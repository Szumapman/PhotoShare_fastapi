import abc

from fastapi import File

from src.database.models import Photo


class AbstractAvatarProvider(abc.ABC):

    @abc.abstractmethod
    def get_avatar(self, email: str, size: int):
        pass


class AbstractPasswordHandler(abc.ABC):
    @abc.abstractmethod
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        pass

    @abc.abstractmethod
    def get_password_hash(self, password: str) -> str:
        pass


class AbstractPhotoStorageProvider(abc.ABC):
    @abc.abstractmethod
    async def upload_photo(self, photo: File) -> str:
        pass

    @abc.abstractmethod
    async def create_qr_code(self, photo_url: str) -> str:
        pass

    @abc.abstractmethod
    async def delete_photo(self, photo: Photo):
        pass
