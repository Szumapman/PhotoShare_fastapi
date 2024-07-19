from sqlalchemy.orm import Session

from src.conf.constant import (
    PHOTO_NOT_FOUND,
    COMMENT_NOT_FOUND,
    FORBIDDEN_FOR_NOT_OWNER,
)
from src.conf.errors import NotFoundError, ForbiddenError
from src.repository.abstract import AbstractCommentRepo
from src.database.models import Comment, Photo


class PostgresCommentRepo(AbstractCommentRepo):
    """
    This class is an implementation of the AbstractCommentRepo interface to use with the PostgreSQL database.
    """

    def __init__(self, db: Session):
        """
        Constructor.
        :param db: sqlalchemy.orm.Session
        """
        self.db = db

    async def create_comment(
        self, comment_content: str, photo_id: int, user_id: int
    ) -> Comment:
        """
        Create comment in the database.

        :param comment_content: text of comment
        :type comment_content: str
        :param photo_id: id of photo that comment belongs to
        :type photo_id: int
        :param user_id: id of user that created comment
        :type user_id: int
        :return: comment
        :rtype: Comment
        """
        comment = Comment(content=comment_content, photo_id=photo_id, user_id=user_id)
        self.db.add(comment)
        self.db.commit()
        self.db.refresh(comment)
        return comment

    async def get_comments(self, photo_id: int) -> list[Comment]:
        """
        Get all comments for a photo.

        :param photo_id: id of photo to get comments for
        :type photo_id: int
        :return: list of comments
        :rtype: list[Comment]
        """
        return self.db.query(Comment).filter(Comment.photo_id == photo_id).all()

    async def get_comment_by_id(self, comment_id: int) -> Comment:
        """
        Get comment by id.

        :param comment_id: id of comment to get
        :type comment_id: int
        :return: comment
        :rtype: Comment
        """
        comment = self.db.query(Comment).filter(Comment.id == comment_id).first()
        if comment is None:
            raise NotFoundError(detail=COMMENT_NOT_FOUND)
        return comment

    async def update_comment(
        self, comment_id: int, user_id: int, comment_content: str
    ) -> Comment:
        """
        Update comment in the database.

        :param comment_id: id of comment to update
        :type comment_id: int
        :param user_id: id of user that updated comment
        :type user_id: int
        :param comment_content: new comment content
        :type comment_content: str
        :return: updated comment
        :rtype: Comment
        """
        comment = await self.get_comment_by_id(comment_id)
        if comment.user_id != user_id:
            raise ForbiddenError(detail=FORBIDDEN_FOR_NOT_OWNER)
        comment.content = comment_content
        self.db.commit()
        self.db.refresh(comment)
        return comment

    async def delete_comment(self, comment_id: int) -> Comment:
        """
        Delete comment in the database.

        :param comment_id: id of comment to delete
        :type comment_id: int
        :return: deleted comment
        :rtype: Comment
        """
        comment = await self.get_comment_by_id(comment_id)
        self.db.delete(comment)
        self.db.commit()
        return comment
