from libgravatar import Gravatar

from src.services.abstract import AbstractAvatarProvider
from src.conf.logger import logger


class AvatarProviderGravatar(AbstractAvatarProvider):
    """
    This class is an implementation of the AbstractAvatarProvider interface to use with the Gravatar service.
    """

    def __init__(self):
        self.gravatar = None

    def get_avatar(self, email: str, size: int) -> str | None:
        """
        Returns url to avatar image for provided email and size

        :param email: email of user to create avatar for
        :type email: str
        :param size: size of avatar to get
        :type size: int
        :return: url to avatar image
        :rtype: str
        """
        try:
            self.gravatar = Gravatar(email)
            return self.gravatar.get_image(size=size)
        except Exception as e:
            logger.error(e)
            return None
