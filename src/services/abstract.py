import abc

from fastapi import File

from src.schemas.photos import PhotoOut, TransformIn


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
    async def upload_avatar(self, avatar: File) -> str:
        pass

    @abc.abstractmethod
    async def delete_photo(self, photo_url: str):
        pass

    @abc.abstractmethod
    async def delete_avatar(self, avatar_url: str):
        pass

    @abc.abstractmethod
    async def transform_photo(
        self, photo_url: str, transform: TransformIn
    ) -> (str, list[str]):
        pass


class AbstractQrCodeProvider(abc.ABC):
    @abc.abstractmethod
    async def stream_qr_code(self, url: str):
        pass
