from sqlalchemy.orm import Session

from src.conf.constant import (
    PHOTO_NOT_FOUND,
    USER_NOT_FOUND,
    FORBIDDEN_FOR_NOT_OWNER_AND_MODERATOR,
    ROLE_ADMIN,
)
from src.database.models import Photo, Tag, User
from src.repository.abstract import AbstractPhotoRepo
from src.schemas.photos import PhotoIn
from src.schemas.users import UserRoleIn


class PostgresPhotoRepo(AbstractPhotoRepo):
    def __init__(self, db: Session):
        self.db = db

    async def upload_photo(
        self,
        current_user_id: int,
        photo_info: PhotoIn,
        photo_url: str,
        qr_code_url: str,
    ) -> Photo:
        photo_tags = []
        for tag in photo_info.tags:
            tag_name = tag.name.strip().lower()
            if tag_name:
                tag = self.db.query(Tag).filter(Tag.name == tag_name).first()
                if tag is None:
                    tag = Tag(name=tag_name)
                self.db.add(tag)
                self.db.commit()
                self.db.refresh(tag)
                photo_tags.append(tag)
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

    async def get_photo_by_id(self, photo_id: int) -> Photo | str:
        photo = self.db.query(Photo).filter(Photo.id == photo_id).first()
        if not photo:
            return PHOTO_NOT_FOUND
        return photo

    async def delete_photo(self, photo_id: int, user_id: int) -> Photo | str:
        user = self.db.query(User).filter(User.id == user_id).first()
        photo = self.db.query(Photo).filter(Photo.id == photo_id).first()
        if user.role != ROLE_ADMIN or photo.user_id != user_id:
            return FORBIDDEN_FOR_NOT_OWNER_AND_MODERATOR
        self.db.delete(photo)
        self.db.commit()
        return photo
