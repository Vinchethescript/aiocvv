from typing import TypedDict, Any, Dict, Union
from datetime import date, datetime


class OKResponse(TypedDict):
    created_at: int
    content: Any
    headers: Dict[str, str]
    status: int
    status_reason: str


class ErrorResponseContent(TypedDict):
    statusCode: int
    error: str


class ErrorResponse(OKResponse):
    content: ErrorResponseContent


Response = Union[OKResponse, ErrorResponse]

Date = Union[date, datetime]
