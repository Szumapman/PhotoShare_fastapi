import abc

from fastapi import File

from src.schemas.photos import PhotoOut, TransformIn


class AbstractAvatarProvider(abc.ABC):
    """
    Abstract class for avatar provider
    """

    @abc.abstractmethod
    def get_avatar(self, email: str, size: int):
        """
        Returns avatar image for provided email and size

        :param email: email of user to create avatar for
        :type email: str
        :param size: size of avatar to get
        :type size: int
        :return: url to avatar image
        :rtype: str
        """
        pass


class AbstractPasswordHandler(abc.ABC):
    """
    Abstract class for password handler
    """

    @abc.abstractmethod
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verifies password hash against plain password

        :param plain_password: plain password to verify
        :type plain_password: str
        :param hashed_password:  hashed password to verify against
        :type hashed_password: str
        :return: True if password is valid, False otherwise
        :rtype: bool
        """
        pass

    @abc.abstractmethod
    def get_password_hash(self, password: str) -> str:
        """
        Returns hashed password

        :param password: password to hash
        :type password: str
        :return: hashed password
        :rtype: str
        """
        pass


class AbstractPhotoStorageProvider(abc.ABC):
    """
    Abstract class for photo storage provider
    """

    @abc.abstractmethod
    async def upload_photo(self, photo: File) -> str:
        """
        Uploads photo to storage

        :param photo: photo file to upload
        :type photo: File
        :return: url to photo in storage
        :rtype: str
        """
        pass

    @abc.abstractmethod
    async def upload_avatar(self, avatar: File) -> str:
        """
        Uploads user avatar to storage

        :param avatar: avatar file to upload
        :type avatar: File
        :return: url to avatar in storage
        :rtype: str
        """
        pass

    @abc.abstractmethod
    async def delete_photo(self, photo_url: str):
        """
        Deletes photo from storage

        :param photo_url: url to photo to delete
        :type photo_url: str
        :return: None
        """
        pass

    @abc.abstractmethod
    async def delete_avatar(self, avatar_url: str):
        """
        Deletes avatar from storage

        :param avatar_url: url to avatar to delete
        :type avatar_url: str
        :return: None
        """
        pass

    @abc.abstractmethod
    async def transform_photo(
        self, photo_url: str, transform: TransformIn
    ) -> (str, list[str]):
        """
        Transforms photo based on provided transform parameters

        :param photo_url: url to photo to transform
        :type photo_url: str
        :param transform: parameters to transform photo
        :type transform: TransformIn
        :return: url to transformed photo and list of transformation parameters
        :rtype: tuple[str, list[str]]
        """
        pass


class AbstractQrCodeProvider(abc.ABC):
    """
    Abstract class for QR code provider
    """

    @abc.abstractmethod
    async def stream_qr_code(self, url: str):
        """
        Streams QR code image for provided url

        :param url: photo url to create QR code for
        :type url: str
        :return: StreamingResponse object with QR code image
        :rtype: StreamingResponse
        """
        pass
