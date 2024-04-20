"""
Type hints that are used across the whole project.
"""

from typing import TypedDict, Any, Dict, Union, TypeVar
from datetime import date, datetime
from .errors import ClassevivaError


class OKResponse(TypedDict):
    """
    Type hint for a successful response.
    """

    created_at: int
    content: Any
    headers: Dict[str, str]
    status: int
    status_reason: str


class ErrorResponseContent(TypedDict):
    """
    Type hint for the content of an error response.
    """

    statusCode: int
    error: str


class ErrorResponse(OKResponse):
    """
    Type hint for an error response.
    """

    content: ErrorResponseContent


Response = Union[OKResponse, ErrorResponse]

Date = Union[date, datetime]

CVVErrors = TypeVar("CVVErrors", bound=ClassevivaError)
AnyCVVError = Union[ClassevivaError, CVVErrors]  # pylint: disable=invalid-name
