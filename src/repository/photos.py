from typing import Type

from sqlalchemy.orm import Session
from sqlalchemy import or_
from src.conf.constant import (
    PHOTO_NOT_FOUND,
    USER_NOT_FOUND,
    FORBIDDEN_FOR_NOT_OWNER_AND_MODERATOR,
    FORBIDDEN_FOR_NOT_OWNER,
    ROLE_ADMIN,
)
from src.conf.errors import NotFoundError, ForbiddenError
from src.database.models import Photo, Tag, User
from src.repository.abstract import AbstractPhotoRepo
from src.schemas.photos import PhotoIn
from src.schemas.tags import TagIn


class PostgresPhotoRepo(AbstractPhotoRepo):
    def __init__(self, db: Session):
        self.db = db

    async def _set_tags(self, photo_tags: list[TagIn]) -> list[Tag]:
        tags = []
        for tag in photo_tags:
            tag_name = tag.name.strip().lower()
            if tag_name:
                tag = self.db.query(Tag).filter(Tag.name == tag_name).first()
                if tag is None:
                    tag = Tag(name=tag_name)
                self.db.add(tag)
                self.db.commit()
                self.db.refresh(tag)
                tags.append(tag)
        return tags

    async def upload_photo(
        self,
        current_user_id: int,
        photo_info: PhotoIn,
        photo_url: str,
        qr_code_url: str,
    ) -> Photo:
        photo_tags = await self._set_tags(photo_info.tags)
        new_photo = Photo(
            user_id=current_user_id,
            photo_url=photo_url,
            qr_url=qr_code_url,
            description=photo_info.description,
            tags=photo_tags,
        )
        self.db.add(new_photo)
        self.db.commit()
        self.db.refresh(new_photo)
        return new_photo

    async def get_photo_by_id(self, photo_id: int) -> Photo:
        photo = self.db.query(Photo).filter(Photo.id == photo_id).first()
        if not photo:
            raise NotFoundError(detail=PHOTO_NOT_FOUND)
        return photo

    async def delete_photo(self, photo_id: int, user_id: int, user_role: str) -> Photo:
        photo = await self.get_photo_by_id(photo_id)
        if photo.user_id == user_id or user_role == ROLE_ADMIN:
            self.db.delete(photo)
            self.db.commit()
            return photo
        raise ForbiddenError(detail=FORBIDDEN_FOR_NOT_OWNER_AND_MODERATOR)

    async def update_photo(
        self, photo_id: int, photo_info: PhotoIn, user_id: int
    ) -> Photo:
        photo = self.db.query(Photo).filter(Photo.id == photo_id).first()
        if not photo:
            raise NotFoundError(detail=PHOTO_NOT_FOUND)
        if user_id != photo.user_id:
            raise ForbiddenError(detail=FORBIDDEN_FOR_NOT_OWNER)
        photo.description = photo_info.description
        if photo_info.tags:
            photo.tags = await self._set_tags(photo_info.tags)
        self.db.commit()
        self.db.refresh(photo)
        return photo

    async def get_photos(
        self,
        query: str | None = None,
        user_id: int | None = None,
        sort_by: str | None = None,
    ) -> list[Type[Photo]]:
        query_base = self.db.query(Photo)
        if query:
            query_base = query_base.filter(
                or_(
                    Photo.description.ilike(f"%{query}%"),
                    Photo.tags.any(Tag.name.ilike(f"%{query}%")),
                )
            )
        # 0 is for return USER_NOT_FOUND when user put 0 as user_id
        if user_id or user_id == 0:
            user = self.db.query(User).filter(User.id == user_id).first()
            if user is None:
                raise NotFoundError(detail=USER_NOT_FOUND)
            query_base = query_base.filter(Photo.user_id == user_id)
        if sort_by:
            field, sort = sort_by.split("-")
            if field == "upload_date":
                query_base = query_base.order_by(
                    Photo.uploaded_at.desc()
                    if sort == "desc"
                    else Photo.uploaded_at.asc()
                )
            elif field == "rating":
                query_base = query_base.order_by(
                    Photo.average_rating.desc()
                    if sort == "desc"
                    else Photo.average_rating.asc()
                )
        photos = query_base.all()
        return photos

    async def add_transform_photo(
        self, photo_id: int, transform_params: list[str], transformation_url: str
    ) -> Photo:
        photo = self.db.query(Photo).filter(Photo.id == photo_id).first()
        if not photo:
            raise NotFoundError(detail=PHOTO_NOT_FOUND)
        transformations = photo.transformations or {}
        photo.transformations = None
        self.db.commit()
        transformations[transformation_url] = transform_params
        photo.transformations = transformations
        self.db.commit()
        self.db.refresh(photo)
        return photo
