"""
Set the configuration settings for the app.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuration settings.

    :param postgres_db: PostgreSQL database name.
    :type postgres_db: str
    :param postgres_user: PostgreSQL username.
    :type postgres_user: str
    :param postgres_password: PostgreSQL password.
    :type postgres_password: str
    :param postgres_host: PostgreSQL host.
    :type postgres_host: str
    :param postgres_port: PostgreSQL port.
    :type postgres_port: int
    :param sqlalchemy_database_url: SQLAlchemy database URL.
    :type sqlalchemy_database_url: str
    :param secret_key: Secret key for
    :type secret_key: str
    :param algorithm: Algorithm for token generation (e.g., "HS256").
    :type algorithm: str
    :param redis_host: Redis server hostname.
    :type redis_host: str
    :param redis_port: Redis server port.
    :type redis_port: int
    :param redis_password: Redis server password.
    :type redis_password: str
    :param cloudinary_name: Cloudinary account name.
    :type cloudinary_name: str
    :param cloudinary_api_key: Cloudinary API key.
    :type cloudinary_api_key: str
    :param cloudinary_api_secret: Cloudinary API secret.
    :type cloudinary_api_secret: str
    :var model_config: Configuration settings for pydantic-settings.
    :type model_config: SettingsConfigDict
    """

    postgres_db: str
    postgres_user: str
    postgres_password: str
    postgres_host: str
    postgres_port: int
    sqlalchemy_database_url: str
    secret_key: str
    algorithm: str
    redis_host: str
    redis_port: int
    redis_password: str
    cloudinary_name: str
    cloudinary_api_key: str
    cloudinary_api_secret: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
