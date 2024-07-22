import abc
from datetime import datetime
from typing import Type

from src.schemas.users import UserIn, ActiveStatus, UserRoleIn
from src.database.models import User, Photo, Rating, Comment, Tag
from src.schemas.photos import PhotoIn, RatingIn


class AbstractUserRepo(abc.ABC):
    """
    Abstract class for user repository
    """

    @abc.abstractmethod
    async def get_user_by_email(self, email: str) -> User | None:
        """
        Returns user from database based on provided email

        :param email: email of user to get from database
        :type email: str
        :return: user from database or None if user not found
        :rtype: User | None
        """
        pass

    @abc.abstractmethod
    async def get_user_by_username(self, username: str) -> User | None:
        """
        Returns user from database based on provided username

        :param username: username of user to get from database
        :type username: str
        :return: user from database or None if user not found
        :rtype: User | None
        """
        pass

    @abc.abstractmethod
    async def get_user_by_id(self, user_id: int) -> User:
        """
        Returns user from database based on provided user id

        :param user_id: user id of user to get from database
        :type user_id: int
        :return: user from database
        :rtype: User
        """
        pass

    @abc.abstractmethod
    async def get_users(self) -> list[Type[User]]:
        """
        Returns users from database

        :return: list of users
        :rtype: list[User]
        """
        pass

    @abc.abstractmethod
    async def create_user(self, user: UserIn, avatar: str) -> User:
        """
        Creates new user in database

        :param user: user data to create
        :type user: UserIn
        :param avatar: avatar url
        :type avatar: str
        :return: created user
        :rtype: User
        """
        pass

    @abc.abstractmethod
    async def update_user(self, new_user_data: UserIn, user_id: int) -> User:
        """
        Updates user in database

        :param new_user_data: new user data
        :type new_user_data: UserIn
        :param user_id: id of user to update
        :type user_id: int
        :return: updated user
        :rtype: User
        """
        pass

    @abc.abstractmethod
    async def update_user_avatar(self, user_id: int, new_avatar_url: str) -> User:
        """
        Updates user avatar in database

        :param user_id: id of user to update avatar
        :type user_id: int
        :param new_avatar_url: new avatar url
        :type new_avatar_url: str
        :return: updated user
        :rtype: User
        """
        pass

    @abc.abstractmethod
    async def delete_user(self, user_id: int) -> User:
        """
        Deletes user from database

        :param user_id: id of user to delete
        :type user_id: int
        :return: deleted user
        :rtype: User
        """
        pass

    @abc.abstractmethod
    async def add_refresh_token(
        self,
        user_id: int,
        token: str | None,
        expiration_date: datetime,
        session_id: str,
    ) -> None:
        """
        Adds refresh token to database

        :param user_id: id of user to add refresh token
        :type user_id: int
        :param token: refresh token
        :type token: str
        :param expiration_date: expiration date of refresh token
        :type expiration_date: datetime
        :param session_id: id of current session
        :type session_id: str
        :return: None
        """
        pass

    @abc.abstractmethod
    async def delete_refresh_token(self, token: str, user_id: int) -> None:
        """
        Deletes refresh token from database

        :param token: token to delete
        :type token: str
        :param user_id: id of user who token belongs to
        :type user_id: int
        :return: None
        """
        pass

    @abc.abstractmethod
    async def logout_user(self, token: str, session_id: str, user: User) -> User:
        """
        Saves user logout data in database

        :param token: user refresh token to save
        :type token: str
        :param session_id: current session id to save
        :type session_id: str
        :param user: user to logout
        :return: logged-out user
        """
        pass

    @abc.abstractmethod
    async def is_user_logout(self, token: str) -> bool:
        """
        Checks if user is logged out

        :param token: user refresh token to check
        :type token: str
        :return: True if user is logged out, False otherwise
        :rtype: bool
        """
        pass

    @abc.abstractmethod
    async def set_user_active_status(
        self, user_id: int, active_status: ActiveStatus, current_user: User
    ) -> User:
        """
        Sets user active status in database
        :param user_id: user id to set active status
        :type user_id: int
        :param active_status: new active status
        :type active_status: ActiveStatus
        :param current_user: user who performed action
        :return: updated user
        :rtype: User
        """
        pass

    @abc.abstractmethod
    async def set_user_role(self, user_id: int, role: UserRoleIn) -> User:
        """
        Sets user role in database
        :param user_id: user id to set role
        :type user_id: int
        :param role: new role
        :type role: UserRoleIn
        :return: updated user
        :rtype: User
        """
        pass


class AbstractPhotoRepo(abc.ABC):
    """
    Abstract class for photo repository
    """

    @abc.abstractmethod
    async def upload_photo(
        self,
        user_id: int,
        photo_info: PhotoIn,
        photo_url: str,
    ) -> Photo:
        """
        Uploads photo to database

        :param user_id: id of user who uploaded photo
        :type user_id: int
        :param photo_info: photo data to upload
        :type photo_info: PhotoIn
        :param photo_url: url of uploaded photo
        :type photo_url: str
        :return: uploaded photo
        :rtype: Photo
        """
        pass

    @abc.abstractmethod
    async def get_photos(
        self,
        skip: int,
        limit: int,
        query: str,
        user_id: int,
        sort_by: str,
    ) -> list[Type[Photo]]:
        """
        Gets photos from database

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
        """
        pass

    @abc.abstractmethod
    async def get_photo_by_id(self, photo_id: int) -> Photo:
        """
        Gets photo from database by id

        :param photo_id: id of photo to get
        :type photo_id: int
        :return: photo
        :rtype: Photo
        """
        pass

    @abc.abstractmethod
    async def delete_photo(self, photo_id: int, user_id: int, user_role: str) -> Photo:
        """
        Deletes photo from database

        :param photo_id: id of photo to delete
        :type photo_id: int
        :param user_id: id of user who deleted photo
        :type user_id: int
        :param user_role: role of user who deleted photo
        :type user_role: str
        :return: deleted photo
        :rtype: Photo
        """
        pass

    @abc.abstractmethod
    async def update_photo(
        self, photo_id: int, photo_info: PhotoIn, user_id: int
    ) -> Photo:
        """
        Updates photo in database

        :param photo_id: id of photo to update
        :type photo_id: int
        :param photo_info: new photo data
        :type photo_info: PhotoIn
        :param user_id: id of user who updated photo
        :type user_id: int
        :return: updated photo
        :rtype: Photo
        """
        pass

    @abc.abstractmethod
    async def add_transform_photo(
        self, photo_id: int, transform_params: list[str], transform_url: str
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
        pass

    @abc.abstractmethod
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
        :return: new rating
        :rtype: Rating
        """
        pass

    @abc.abstractmethod
    async def delete_rating(self, photo_id: int, user_id: int) -> Rating:
        """
        Deletes rating from photo in database

        :param photo_id: id of photo to delete rating from
        :type photo_id: int
        :param user_id: id of user who deleted rating
        :type user_id: int
        :return: updated photo
        :rtype: Rating
        """


class AbstractCommentRepo(abc.ABC):
    """
    Abstract class for comment repository
    """

    @abc.abstractmethod
    async def create_comment(
        self, comment_content: str, photo_id: int, user_id: int
    ) -> Comment:
        """
        Creates comment in database

        :param comment_content: text of comment
        :type comment_content: str
        :param photo_id: id of photo that comment belongs to
        :type photo_id: int
        :param user_id: id of user that created comment
        :type user_id: int
        """
        pass

    @abc.abstractmethod
    async def get_comments(self, photo_id: int) -> list[Comment]:
        """
        Gets comments for a photo from database

        :param photo_id: id of photo to get comments for
        :type photo_id: int
        :return: list of comments
        :rtype: list[Comment]
        """
        pass

    @abc.abstractmethod
    async def get_comment_by_id(self, comment_id: int) -> Comment:
        """
        Gets comment from database by id

        :param comment_id: id of comment to get
        :type comment_id: int
        :return: comment
        :rtype: Comment
        """
        pass

    @abc.abstractmethod
    async def update_comment(
        self, comment_id: int, user_id: int, comment_content: str
    ) -> Comment:
        """
        Updates comment in database

        :param comment_id:
        :param user_id:
        :param comment_content:
        :return:
        """
        pass

    @abc.abstractmethod
    async def delete_comment(self, comment_id: int) -> Comment:
        """
        Delete comment in the database.

        :param comment_id: id of comment to delete
        :type comment_id: int
        :return: deleted comment
        :rtype: Comment
        """
        pass


class AbstractTagRepo(abc.ABC):
    """
    Abstract class for tag repository
    """

    @abc.abstractmethod
    async def get_tag_by_name(self, tag_name: str) -> Tag | None:
        """
        Gets tag from database by name

        :param tag_name: name of tag to get
        :type tag_name: str
        :return: tag or None if not found
        :rtype: Tag | None
        """
        pass

    @abc.abstractmethod
    async def create_tag(self, tag_name: str) -> Tag:
        """
        Create a new tag.

        :param tag_name: tag name
        :type tag_name: str
        :return: new tag
        :rtype: Tag
        """
        pass

    @abc.abstractmethod
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
        pass

    @abc.abstractmethod
    async def get_tag_by_id(self, tag_id: int) -> Tag:
        """
        Gets tag from database by id

        :param tag_id: id of tag to get
        :type tag_id: int
        :return: tag
        :rtype: Tag
        """
        pass

    @abc.abstractmethod
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
        pass

    @abc.abstractmethod
    async def delete_tag(self, tag_id: int) -> Tag:
        """
        Deletes tag from database

        :param tag_id: id of tag to delete
        :type tag_id: int
        :return: deleted tag
        :rtype: Tag
        """
        pass
