from typing import Type

from sqlalchemy.orm import Session
from sqlalchemy import or_
from src.conf.constant import (
    PHOTO_NOT_FOUND,
    USER_NOT_FOUND,
    FORBIDDEN_FOR_NOT_OWNER_AND_MODERATOR,
    FORBIDDEN_FOR_NOT_OWNER,
    ROLE_ADMIN,
    FORBIDDEN_FOR_OWNER,
    RATING_NOT_FOUND,
)
from src.conf.errors import NotFoundError, ForbiddenError
from src.database.models import Photo, Tag, User, Rating
from src.repository.abstract import AbstractPhotoRepo
from src.schemas.photos import PhotoIn, RatingIn
from src.schemas.tags import TagIn


class PostgresPhotoRepo(AbstractPhotoRepo):
    """
    This class is an implementation of the AbstractPhotoRepo interface to use with the PostgreSQL database.
    """

    def __init__(self, db: Session):
        """
        Constructor.
        :param db: sqlalchemy.orm.Session
        """
        self.db = db

    async def _set_tags(self, photo_tags: list[TagIn]) -> list[Tag]:
        """
        Helper function to set tags in the database.

        :param photo_tags: list of tags to set
        :type: list[TagIn]
        :return: list of tags
        :rtype: list[Tag]
        """
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
        user_id: int,
        photo_info: PhotoIn,
        photo_url: str,
    ) -> Photo:
        """
        Uploads a photo to the database.

        :param user_id: id of user who uploaded photo
        :type user_id: int
        :param photo_info: data of photo to upload
        :type photo_info: PhotoIn
        :param photo_url: url of uploaded photo
        :type photo_url: str
        :return: uploaded photo
        :rtype: Photo
        """
        photo_tags = await self._set_tags(photo_info.tags)
        new_photo = Photo(
            user_id=user_id,
            photo_url=photo_url,
            description=photo_info.description,
            tags=photo_tags,
        )
        self.db.add(new_photo)
        self.db.commit()
        self.db.refresh(new_photo)
        return new_photo

    async def get_photo_by_id(self, photo_id: int) -> Photo:
        """
        Gets photo from database by id.
        :param photo_id: id of photo to get
        :type photo_id: int
        :return: photo
        :rtype: Photo
        :raises: NotFoundError: if photo is not found
        """
        photo = self.db.query(Photo).filter(Photo.id == photo_id).first()
        if not photo:
            raise NotFoundError(detail=PHOTO_NOT_FOUND)
        return photo

    async def delete_photo(self, photo_id: int, user_id: int, user_role: str) -> Photo:
        """
        Deletes photo from database.
        :param photo_id: id of photo to delete
        :type photo_id: int
        :param user_id: id of user who deleted photo
        :type user_id: int
        :param user_role: role of user who deleted photo
        :type user_role: str
        :return: deleted photo
        :rtype: Photo
        :raises: ForbiddenError: if user is not owner and not admin
        """
        photo = await self.get_photo_by_id(photo_id)
        if photo.user_id == user_id or user_role == ROLE_ADMIN:
            self.db.delete(photo)
            self.db.commit()
            return photo
        raise ForbiddenError(detail=FORBIDDEN_FOR_NOT_OWNER_AND_MODERATOR)

    async def update_photo(
        self, photo_id: int, photo_info: PhotoIn, user_id: int
    ) -> Photo:
        """
        Updates photo in database.
        :param photo_id: id of photo to update
        :type photo_id: int
        :param photo_info: new photo data
        :type photo_info: PhotoIn
        :param user_id: id of user who updated photo
        :type user_id: int
        :return: updated photo
        :rtype: Photo
        :raises: ForbiddenError: if user is not owner of photo
        """
        photo = await self.get_photo_by_id(photo_id)
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
        skip: int,
        limit: int,
        query: str | None = None,
        user_id: int | None = None,
        sort_by: str | None = None,
    ) -> list[Type[Photo]]:
        """
        Gets photos from database.

        :param skip: number of photos to skip
        :type skip: int
        :param limit: number of photos to get
        :type limit: int
        :param query: query to search photos by
        :type query: str
        :param user_id: id of the user whose photos we are looking for
        :type user_id: int
        :param sort_by: how to sort returned photos
        :return: list of photos
        :rtype: list[Type[Photo]]
        :raises: NotFoundError: if user whose photos we are looking for not found in database
        """
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
        photos = query_base.offset(skip).limit(limit).all()
        return photos

    async def add_transform_photo(
        self, photo_id: int, transform_params: list[str], transformation_url: str
    ) -> Photo:
        """
        Adds transform to photo in database

        :param photo_id: id of photo to add transform to
        :type photo_id: int
        :param transform_params: list of transform params
        :type transform_params: list[str]
        :param transform_url: url to transformed photo
        :type transform_url: str
        :return: updated photo
        :rtype: Photo
        """
        photo = await self.get_photo_by_id(photo_id)
        transformations = photo.transformations or {}
        photo.transformations = None
        self.db.commit()
        if len(transformations) == 0:
            key = 1
        else:
            max_value = 0
            for key in transformations:
                if int(key) > max_value:
                    max_value = int(key)
            key = max_value + 1
        transformations[key] = [transformation_url, transform_params]
        photo.transformations = transformations
        self.db.commit()
        self.db.refresh(photo)
        return photo

    async def rate_photo(
        self, photo_id: int, rating_in: RatingIn, user_id: int
    ) -> Rating:
        """
        Rates photo in database

        :param photo_id: id of photo to rate
        :type photo_id: int
        :param rating_in: new rating
        :type rating_in: RatingIn
        :param user_id: id of user who rated photo
        :type user_id: int
        :return: updated photo
        :rtype: Photo
        """
        photo = await self.get_photo_by_id(photo_id)
        if user_id == photo.user_id:
            raise ForbiddenError(detail=FORBIDDEN_FOR_OWNER)
        rating = (
            self.db.query(Rating)
            .filter(Rating.photo_id == photo_id, Rating.user_id == user_id)
            .first()
        )
        if rating is None:
            rating = Rating(photo_id=photo_id, user_id=user_id, score=rating_in.score)
            self.db.add(rating)
        else:
            rating.score = rating_in.score
        self.db.commit()
        self.db.refresh(rating)
        return rating

    async def delete_rating(self, photo_id: int, user_id: int) -> Rating:
        """
        Deletes rating from photo in database

        :param photo_id: id of photo to delete rating from
        :type photo_id: int
        :param user_id: id of user who rated photo
        :type user_id: int
        :return: deleted rating
        :rtype: Rating
        """
        rating = (
            self.db.query(Rating)
            .filter(Rating.photo_id == photo_id, Rating.user_id == user_id)
            .first()
        )
        if rating is None:
            raise NotFoundError(detail=RATING_NOT_FOUND)
        self.db.delete(rating)
        self.db.commit()
        return rating
