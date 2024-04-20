"""
Useful functions used inside the library.
"""

from datetime import datetime, date, timedelta
from typing import Union, Type, Callable, Optional
from .errors import ClassevivaError
from .types import AnyCVVError


def create_repr(self, **kwargs):
    """
    Create a __repr__ string for a class.
    """
    params = []
    for k, v in kwargs.items():
        if v is not None:
            if isinstance(v, list):
                v = len(v)

            params.append(f"{k}={v!r}")

    return f"<{type(self).__name__} {' '.join(params)}>"


def convert_date(date_: Union[datetime, date], today: bool = False) -> str:
    """
    Convert a date to a string.
    """
    date_ = getattr(date_, "date", lambda: date_)()
    if today and date_ in [date.today(), date.today() - timedelta(days=1)]:
        return "today" if date_ == date.today() else "yesterday"

    return date_.strftime("%Y%m%d")


def __recurse_subclasses(cls: Type):
    for sub in cls.__subclasses__():
        yield sub
        yield from __recurse_subclasses(sub)


def find_exc(
    response: dict, base: Type[ClassevivaError] = ClassevivaError
) -> AnyCVVError:
    """
    Find the correct exception to raise based
    on the response from the Classeviva API.
    """
    content = response["content"]
    tp = content["error"].split("/")[1]
    status = response["status"]
    if not issubclass(base, ClassevivaError):
        raise ValueError("base must derive from ClassevivaError")

    if tp == "authentication failed":
        sc = content["info"]
    elif status < 200 or status >= 300:
        sc = response["status_reason"].replace(" ", "")

    exc = base(response)
    for sub in __recurse_subclasses(base):
        if sub.__name__ == sc:
            exc = sub(response)
            break

    return exc


def capitalize_name(string: str):
    """
    Capitalizes a name.
    """
    return " ".join(word.capitalize() for word in string.split())


def parse_date(string: str):
    """
    Converts a date string in the YYYY-mm-dd format to a date object.
    """
    return datetime.strptime(string, "%Y-%m-%d").date()


def parse_time(string: str):
    """
    Converts a time string in the YYYY-mm-ddTHH:MM:SS+HH:MM format to a datetime object.
    """
    return datetime.strptime(string, "%Y-%m-%dT%H:%M:%S%z")


def group_by_date(
    data: list, parser: Optional[Callable] = None, *args, **kwargs
):  # pylint: disable=keyword-arg-before-vararg
    """
    Groups a list of events by date.
    """
    ret = {}
    for dt in data:
        date_ = (
            parse_time(dt["evtDatetimeBegin"]).date()
            if "evtDatetimeBegin" in dt
            else parse_date(dt["evtDate" if "evtDate" in dt else "dayDate"])
        )

        if date_ not in ret:
            ret[date_] = []

        ret[date_].append(parser(dt, *args, **kwargs) if parser else dt)

    return ret
