from libgravatar import Gravatar

from src.services.abstract import AbstractAvatarProvider
from src.conf.logger import logger


class AvatarProviderGravatar(AbstractAvatarProvider):

    def __init__(self):
        self.gravatar = None

    def get_avatar(self, email: str, size: int) -> str | None:
        try:
            self.gravatar = Gravatar(email)
            return self.gravatar.get_image(size=size)
        except Exception as e:
            logger.error(e)
            return None
