from datetime import datetime, date, timedelta
from typing import Union, Type
from .errors import ClassevivaError


def create_repr(self, **kwargs):
    params = []
    for k, v in kwargs.items():
        if v is not None:
            if isinstance(v, list):
                v = len(v)

            params.append(f"{k}={v!r}")

    return f"<{type(self).__name__} {' '.join(params)}>"


def convert_date(date: Union[datetime, date], today: bool = False) -> str:
    date = getattr(date, "date", lambda: date)()
    if today and date in [date.today(), date.today() - timedelta(days=1)]:
        return "today" if date == date.today() else "yesterday"

    return date.strftime("%Y%m%d")


def __recurse_subclasses(cls: Type):
    for sub in cls.__subclasses__():
        yield sub
        yield from __recurse_subclasses(sub)


def find_exc(response: dict, base: Type[ClassevivaError] = ClassevivaError):
    content = response["content"]
    tp = content["error"].split("/")[1]
    status = response["status"]
    if not issubclass(base, ClassevivaError):
        raise ValueError("base must derive from ClassevivaError")

    if tp == "authentication failed":
        sc = content["info"]
    elif status < 200 or status >= 300:
        sc = response["status_reason"].replace(" ", "")

    for sub in __recurse_subclasses(base):
        print(sub.__name__, sc)
        if sub.__name__ == sc:
            raise sub(response)

    raise base(response)


def capitalize_name(string: str):
    return " ".join(word.capitalize() for word in string.split())


def parse_date(string: str):
    return datetime.strptime(string, "%Y-%m-%d").date()


def parse_time(string: str):
    return datetime.strptime(string, "%Y-%m-%dT%H:%M:%S%z")


def group_by_date(data: list, parser=None, *args, **kwargs):
    ret = {}
    for dt in data:
        date = (
            parse_time(dt["evtDatetimeBegin"]).date()
            if "evtDatetimeBegin" in dt
            else parse_date(dt["evtDate" if "evtDate" in dt else "dayDate"])
        )

        if date not in ret:
            ret[date] = []

        ret[date].append(parser(dt, *args, **kwargs) if parser else dt)

    return ret
