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

from src.conf.constant import (
    MAX_TAG_NAME_LENGTH,
    MAX_COMMENT_LENGTH,
    MAX_USERNAME_LENGTH,
    MAX_DESCRIPTION_LENGTH,
    ROLE_ADMIN,
    ROLE_MODERATOR,
    ROLE_STANDARD,
)

Base = declarative_base()

photo_m2m_tag = Table(
    "photo_m2m_tag",
    Base.metadata,
    Column("id", Integer, primary_key=True),
    Column("photo_id", Integer, ForeignKey("photos.id", ondelete="CASCADE")),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE")),
    UniqueConstraint("photo_id", "tag_id", name="unique_photo_tag"),
)


class Photo(Base):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    photo_url = Column(String(255), nullable=False)
    qr_url = Column(String(255), nullable=False)
    transformation = Column(JSON, nullable=True)
    description = Column(String(MAX_DESCRIPTION_LENGTH), nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", backref="photos")
    tags = relationship("Tag", secondary=photo_m2m_tag, backref="photos")
    comments = relationship("Comment", backref="photo", cascade="all, delete-orphan")
    ratings = relationship("Rating", backref="photo", cascade="all, delete-orphan")

    @hybrid_property
    def average_rating(self):
        ratings_nuber = len(self.ratings)
        if ratings_nuber > 0:
            return sum(rating.score for rating in self.ratings) / ratings_nuber
        return None


class User(Base):
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
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True)
    name = Column(String(MAX_TAG_NAME_LENGTH), nullable=False, unique=True)


class Comment(Base):
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
    __tablename__ = "refresh_tokens"
    id = Column(Integer, primary_key=True)
    refresh_token = Column(String(350), nullable=False, unique=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    session_id = Column(String(150), nullable=False, unique=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)


class LogoutAccessToken(Base):
    __tablename__ = "logout_access_tokens"
    id = Column(Integer, primary_key=True)
    logout_access_token = Column(String(350), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
