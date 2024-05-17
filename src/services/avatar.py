from libgravatar import Gravatar

from src.services.abstract import AbstractAvatarProvider


class AvatarProviderGravatar(AbstractAvatarProvider):

    def get_avatar(self, email: str, size: int) -> str | None:
        try:
            self.gravatar = Gravatar(email)
            return self.gravatar.get_image(size=size)
        except Exception as e:
            print(e)
            return None
