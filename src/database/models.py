from sqlalchemy import (
    Table,
    Column,
    Integer,
    String,
    Boolean,
    Enum,
    ForeignKey,
    JSON,
    UniqueConstraint,
    func,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql.sqltypes import DateTime
from sqlalchemy.orm import relationship, declarative_base

from src.conf.constants import (
    MAX_TAG_NAME_LENGTH,
    MAX_COMMENT_LENGTH,
    MAX_USERNAME_LENGTH,
    MAX_DESCRIPTION_LENGTH,
    ROLE_ADMIN,
    ROLE_MODERATOR,
    ROLE_STANDARD,
)

Base = declarative_base()

"""
This table is used to map tags to photos.
"""
photo_m2m_tag = Table(
    "photo_m2m_tag",
    Base.metadata,
    Column("id", Integer, primary_key=True),
    Column("photo_id", Integer, ForeignKey("photos.id", ondelete="CASCADE")),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE")),
    UniqueConstraint("photo_id", "tag_id", name="unique_photo_tag"),
)


class Photo(Base):
    """
    SQLAlchemy model represents a photo in the database.

    Attributes:
        id (int): Primary key.
        user_id (int): Foreign key to the user who uploaded the photo.
        photo_url (str): URL of the photo.
        transformations (list): List of transformations applied to the photo.
        description (str): Description of the photo.
        uploaded_at (datetime): Datetime when the photo was uploaded.

        user: relationship to the user who uploaded the photo.
        tags: relationship to the tags associated with the photo.
        comments: relationship to the comments associated with the photo.
        ratings: relationship to the ratings associated with the photo.
    """

    __tablename__ = "photos"

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    photo_url = Column(String(255), nullable=False)
    transformations = Column(JSON, nullable=True)
    description = Column(String(MAX_DESCRIPTION_LENGTH), nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", backref="photos")
    tags = relationship("Tag", secondary=photo_m2m_tag, backref="photos")
    comments = relationship("Comment", backref="photo", cascade="all, delete-orphan")
    ratings = relationship("Rating", backref="photo", cascade="all, delete-orphan")

    @hybrid_property
    def average_rating(self):
        if self.ratings:
            return sum(rating.score for rating in self.ratings) / len(self.ratings)
        return None


class User(Base):
    """
    SQLAlchemy model represents a user in the database.

    Attributes:
        id (int): Primary key.
        username (str): Username of the user.
        email (str): Email of the user.
        password (str): user password.
        role (str): Role of the user.
        created_at (datetime): Datetime when the user was created.
        avatar (str): URL of the user's avatar.
        is_active (bool): Whether the user is active or banned.

        refresh_tokens: relationship to the refresh tokens associated with the user.
        comments: relationship to the comments posted by the user.
        ratings: relationship to the ratings given by the user.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(MAX_USERNAME_LENGTH), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password = Column(String(255), nullable=False)
    role = Column(
        Enum(ROLE_ADMIN, ROLE_MODERATOR, ROLE_STANDARD, name="user_role_types"),
        nullable=False,
        default=ROLE_STANDARD,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    avatar = Column(String(255), nullable=True)
    is_active = Column(Boolean(), default=True)

    refresh_tokens = relationship(
        "RefreshToken", backref="user", cascade="all, delete-orphan"
    )
    comments = relationship("Comment", backref="user", cascade="all, delete-orphan")
    ratings = relationship("Rating", backref="user", cascade="all, delete-orphan")


class Tag(Base):
    """
    SQLAlchemy model represents a tag in the database.

    Attributes:
        id (int): Primary key.
        name (str): Name of the tag.
    """

    __tablename__ = "tags"

    id = Column(Integer, primary_key=True)
    name = Column(String(MAX_TAG_NAME_LENGTH), nullable=False, unique=True)


class Comment(Base):
    """
    SQLAlchemy model represents a comment in the database.

    Attributes:
        id (int): Primary key.
        photo_id (int): Foreign key to the photo the comment belongs to.
        user_id (int): Foreign key to the user who posted the comment.
        content (str): Content of the comment.
        created_at (datetime): Datetime when the comment was created.
        updated_at (datetime): Datetime when the comment was updated.
    """

    __tablename__ = "comments"

    id = Column(Integer, primary_key=True)
    photo_id = Column(
        Integer, ForeignKey("photos.id", ondelete="CASCADE"), nullable=False
    )
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    content = Column(String(MAX_COMMENT_LENGTH), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Rating(Base):
    """
    SQLAlchemy model represents a rating in the database.

    Attributes:
        id (int): Primary key.
        photo_id (int): Foreign key to the photo the rating belongs to.
        user_id (int): Foreign key to the user who posted the rating.
        score (int): Score of the rating.
    """

    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True)
    photo_id = Column(
        Integer, ForeignKey("photos.id", ondelete="CASCADE"), nullable=False
    )
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    score = Column(Integer, nullable=False)


class RefreshToken(Base):
    """
    SQLAlchemy model represents a refresh token in the database.

    Attributes:
        id (int): Primary key.
        refresh_token (str): Refresh token.
        user_id (int): Foreign key to the user the refresh token belongs to.
        session_id (str): Session ID of the refresh token.
        expires_at (datetime): Datetime when the refresh token expires.
    """

    __tablename__ = "refresh_tokens"
    id = Column(Integer, primary_key=True)
    refresh_token = Column(String(350), nullable=False, unique=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    session_id = Column(String(150), nullable=False, unique=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)


class LogoutAccessToken(Base):
    """
    SQLAlchemy model represents a logout access token in the database.

    Attributes:
        id (int): Primary key.
        logout_access_token (str): Logout access token.
        expires_at (datetime): Datetime when the logout access token expires.
    """

    __tablename__ = "logout_access_tokens"
    id = Column(Integer, primary_key=True)
    logout_access_token = Column(String(350), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
