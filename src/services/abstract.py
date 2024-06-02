import abc


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
