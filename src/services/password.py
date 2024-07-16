import bcrypt

from src.services.abstract import AbstractPasswordHandler


class BcryptPasswordHandler(AbstractPasswordHandler):
    """
    This class is an implementation of the AbstractPasswordHandler interface to use with the bcrypt library.
    """

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verifies password hash against plain password
        :param plain_password: plain password to verify
        :type plain_password: str
        :param hashed_password: hashed password to verify against
        :type hashed_password: str
        :return: True if password is valid, False otherwise
        :rtype: bool
        """
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )

    def get_password_hash(self, password: str) -> str:
        """
        Returns hashed password

        :param password: password to hash
        :type password: str
        :return: hashed password
        :rtype: str
        """
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
