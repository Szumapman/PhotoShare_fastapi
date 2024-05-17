import abc


class AbstractAvatarProvider(abc.ABC):

    @abc.abstractmethod
    def get_avatar(self, email: str, size: int):
        pass
