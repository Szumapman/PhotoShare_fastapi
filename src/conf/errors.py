from fastapi import HTTPException, status

# from main import app


class PhotoStorageProviderError(Exception):
    """
    Base class for errors related to photo storage providers.

    :param detail: A description of the error.
    """

    def __init__(self, message=None, detail=None):
        super().__init__(message)
        self.detail = detail


class NotFoundError(Exception):
    """
    Raised when a requested resource is not found.

    :param detail: A description what the resource is not found.
    """

    def __init__(self, message=None, detail=None):
        super().__init__(message)
        self.detail = detail


class ForbiddenError(Exception):
    """
    Raised when a user has no permission to do the requested action.

    :param detail: A description of the reason why the user is forbidden.
    """

    def __init__(self, message=None, detail=None):
        super().__init__(message)
        self.detail = detail


class UnauthorizedError(Exception):
    """
    Raised when a user is not authorized to access a resource.

    :param detail: A description of the reason why the user is unauthorized.
    """

    def __init__(self, message=None, detail=None):
        super().__init__(message)
        self.detail = detail


class ConflictError(Exception):
    """
    Raised when you try to create a resource that already exists and must be unique.

    :param detail: A detail of the conflict.
    """

    def __init__(self, message=None, detail=None):
        super().__init__(message)
        self.detail = detail
