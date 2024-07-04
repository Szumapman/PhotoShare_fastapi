from fastapi import HTTPException, status

# from main import app


class PhotoStorageProviderError(Exception):
    def __init__(self, message=None, detail=None):
        super().__init__(message)
        self.detail = detail


class NotFoundError(Exception):
    def __init__(self, message=None, detail=None):
        super().__init__(message)
        self.detail = detail


class ForbiddenError(Exception):
    def __init__(self, message=None, detail=None):
        super().__init__(message)
        self.detail = detail


class UnauthorizedError(Exception):
    def __init__(self, message=None, detail=None):
        super().__init__(message)
        self.detail = detail
