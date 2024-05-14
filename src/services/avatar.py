from libgravatar import Gravatar

from src.services.abstract import AbstractAvatarProvider


class AvatarProviderGravatar(AbstractAvatarProvider):
    def __init__(self, email: str):
        try:
            self.gravatar = Gravatar(email)
        except Exception as e:
            print(e)

    def get_avatar(self, size: int) -> str | None:
        try:
            return self.gravatar.get_image(size=size)
        except Exception as e:
            print(e)
            return None
