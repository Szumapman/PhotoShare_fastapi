from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Configuration settings.

    Attributes:
        postgres_db (str): PostgreSQL database name.
        postgres_user (str): PostgreSQL username.
        postgres_password (str): PostgreSQL password.
        postgres_host (str, optional): PostgreSQL host (default is "localhost").
        postgres_port (int): PostgreSQL port.
        sqlalchemy_database_url (str): SQLAlchemy database URL.
        secret_key (str): Secret key for
        algorithm (str): Algorithm for token generation (e.g., "HS256").
        redis_host (str, optional): Redis server hostname (default is "localhost").
        redis_port (int, optional): Redis server port (default is 6379).
        redis_password (str): Redis server password (default is "password").
        cloudinary_name (str): Cloudinary account name.
        cloudinary_api_key (str): Cloudinary API key.
        cloudinary_api_secret (str): Cloudinary API secret.

    Config:
            env_file (str): Path to the environment file (default is ".env").
            env_file_encoding (str): Encoding of the environment file (default is "utf-8").
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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
