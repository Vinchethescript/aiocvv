from typing import Any, IO


class File:
    def __init__(self, data: IO[Any], filename: str):
        data.seek(0)
        self.__data = data
        self.filename = filename

    @property
    def data(self):
        return self.__data

    def __str__(self):
        return self.filename

    def __repr__(self):
        return f"<File name={self.filename!r}>"
