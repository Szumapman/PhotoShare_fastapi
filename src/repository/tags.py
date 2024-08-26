from typing import Type

from sqlalchemy.orm import Session

from src.conf.constants import TAG_NOT_FOUND, TAG_ALREADY_EXISTS
from src.conf.errors import NotFoundError, ConflictError
from src.repository.abstract import AbstractTagRepo
from src.database.models import Tag


class PostgresTagRepo(AbstractTagRepo):
    """
    This class is an implementation of the AbstractTagRepo interface to use with the PostgreSQL database.
    """

    def __init__(self, db: Session):
        """
        Constructor.
        :param db: sqlalchemy.orm.Session
        """
        self.db = db

    async def get_tag_by_name(self, tag_name: str) -> Tag | None:
        """
        Gets tag from database by name

        :param tag_name: name of tag to get
        :type tag_name: str
        :return: tag or None if not found
        :rtype: Tag | None
        """
        tag_name = tag_name.strip().lower()
        return self.db.query(Tag).filter(Tag.name == tag_name).first()

    async def create_tag(self, tag_name: str) -> Tag:
        """
        Create a new tag.

        :param tag_name: name of tag to create
        :type tag_name: str
        :return: created tag
        :rtype: Tag
        """
        tag_name = tag_name.strip().lower()
        tag = Tag(name=tag_name)
        self.db.add(tag)
        self.db.commit()
        self.db.refresh(tag)
        return tag

    async def get_tags(
        self, sort_by: str | None, skip: int, limit: int
    ) -> list[Type[Tag]]:
        """
        Gets all tags from database

        :param sort_by: how to sort the tags (if not none)
        :type sort_by: str | None
        :param skip: number of tags to skip
        :type skip: int
        :param limit: number of tags to return
        :type limit: int
        :return: list of tags
        :rtype: list[Type[Tag]]
        """
        if sort_by is None:
            return self.db.query(Tag).offset(skip).limit(limit).all()
        else:
            return (
                self.db.query(Tag)
                .order_by(Tag.name.asc() if sort_by == "asc" else Tag.name.desc())
                .offset(skip)
                .limit(limit)
                .all()
            )

    async def get_tag_by_id(
        self,
        tag_id: int,
    ) -> Tag:
        """
        Gets tag from database by id

        :param tag_id: id of tag to get
        :type tag_id: int
        :return: tag
        :rtype: Tag
        """
        tag = self.db.query(Tag).filter(Tag.id == tag_id).first()
        if tag is None:
            raise NotFoundError(detail=TAG_NOT_FOUND)
        return tag

    async def update_tag(self, tag_id: int, tag_name: str) -> Tag:
        """
        Updates tag in database

        :param tag_id: id of tag to update
        :type tag_id: int
        :param tag_name: new name of tag
        :type tag_name: str
        :return: updated tag
        :rtype: Tag
        """
        tag = await self.get_tag_by_id(tag_id)
        if await self.get_tag_by_name(tag_name):
            raise ConflictError(detail=TAG_ALREADY_EXISTS)
        tag.name = tag_name
        self.db.commit()
        self.db.refresh(tag)
        return tag

    async def delete_tag(self, tag_id: int) -> Tag:
        """
        Deletes tag from database

        :param tag_id: id of tag to delete
        :type tag_id: int
        :return: deleted tag
        :rtype: Tag
        """
        tag = await self.get_tag_by_id(tag_id)
        self.db.delete(tag)
        self.db.commit()
        return tag
