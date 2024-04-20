"""
This helper contains the classes that represent the noticeboard and its items.
The noticeboard can be used both by students and teachers.
"""

# pylint: disable=arguments-differ

from typing import Optional, Any, IO, List
from io import BytesIO
from ..modules.core import BaseModule, Noticeboard
from ..types import Response
from ..errors import ClassevivaError


class File:
    """
    Represents a file to upload to the noticeboard.
    """

    def __init__(self, data: IO[Any], filename: str):
        data.seek(0)
        self.__data = data
        self.filename = filename

    @property
    def data(self):
        """The file's data."""
        return self.__data

    def __str__(self):
        return self.filename

    def __repr__(self):
        return f"<File name={self.filename!r}>"


class Attachment(File):
    """
    Represents an attachment of an uploaded noticeboard item.
    """

    def __init__(self, item: "NoticeboardItem", data: dict):
        # pylint: disable=super-init-not-called
        self.filename = data["fileName"]
        self.num = data["attachNum"]
        self.__item = item

    async def download(self):
        """Download the attachment."""
        resp = await self.__item.noticeboard.get_attachment(
            self.__item.code, self.__item.id, self.num
        )
        data = BytesIO(resp["content"])
        super().__init__(data, self.filename)
        return self


class NoticeboardItem:
    """
    Represents an item in the noticeboard.
    """

    def __init__(self, nb: "MyNoticeboard", payload: dict, content: str):
        self.__payload = payload
        self.__content = content
        self.__board = nb
        self.__attachments = []

    @property
    def noticeboard(self):
        """The noticeboard this item belongs to."""
        return self.__board

    @property
    def content(self):
        """The item's content."""
        return self.__content

    @property
    def id(self) -> int:
        """The item's publication ID."""
        return self.__payload["pubId"]

    @property
    def read(self):
        """Whether the item has been read."""
        return self.__payload["readStatus"]

    @property
    def code(self) -> str:
        """The item's event code."""
        return self.__payload["evtCode"]

    @property
    def title(self) -> str:
        """The item's title."""
        return self.__payload["cntTitle"]

    @property
    def category(self) -> str:
        """The item's category."""
        return self.__payload["cntCategory"]

    @property
    def has_changed(self) -> bool:
        """Whether the item has changed."""
        return self.__payload["cntHasChanged"]

    @property
    def attachments(self):
        """The item's attachments."""
        if not self.__attachments:
            for attach in self.__payload["attachments"]:
                self.__attachments.append(Attachment(self, attach))

            self.__attachments = list(sorted(self.__attachments, key=lambda x: x.num))

        return self.__attachments

    async def join(
        self,
        text: Optional[str] = None,
        sign: Optional[bool] = None,
        file: Optional[File] = None,
        *,
        raise_exc: bool = True,
    ) -> bool:
        """
        Join the noticeboard item.

        :param text: The text to send.
        :param sign: Whether to sign the text.
        :param file: The file to upload.
        :param raise_exc: Whether to raise an exception if an error occurs.

        :return: Whether the operation was successful.
        """
        try:
            await self.__board.join(
                self.__payload["evtCode"],
                self.__payload["pubId"],
                text=text,
                filename=file.filename if file else None,
                file=file.data if file else None,
                sign=sign,
                attrs=False,
                include_attachment=False,
                reply_info=False,
            )
        except ClassevivaError:
            if raise_exc:
                raise

            return False

        return True


class MyNoticeboard:
    """
    Represents the noticeboard of a user.
    """

    def __init__(
        self, noticeboard: Noticeboard, id: int
    ):  # pylint: disable=redefined-builtin

        self.noticeboard = noticeboard
        self.id = id
        self.__read = self.noticeboard.read

    async def all(self) -> List[NoticeboardItem]:
        """Get all the items in the noticeboard."""
        ret = []
        async for item in self:
            ret.append(item)
        return ret

    async def __get(
        self, code: str, id: int  # pylint: disable=redefined-builtin
    ) -> Response:
        items = await self.noticeboard.all(self.id)
        for item in items["content"]["items"]:
            if id == item["pubId"] and code == item["evtCode"]:
                return item

    async def read(self, event_code: str, publication_id: int) -> Response:
        """
        Read a noticeboard item.

        :param event_code: The event code of the item.
        :param publication_id: The publication ID of the item.

        :return: The response from the Classeviva API.
        """
        payload = await self.__get(event_code, publication_id)
        data = await self.__read(self.id, event_code, publication_id)

        return NoticeboardItem(self, payload, data["content"]["item"]["text"])

    async def join(
        self,
        event_code: str,
        publication_id: int,
        *,
        text: Optional[str] = None,
        file: Optional[IO[Any]] = None,
        filename: Optional[str] = None,
        sign: Optional[bool] = None,
        attrs: bool = True,
        include_attachment: bool = False,
        reply_info: bool = False,
        multi: bool = False,
    ) -> Response:
        """
        Join a noticeboard item.

        :param event_code: The event code of the item.
        :param publication_id: The publication ID of the item.
        """
        return await self.noticeboard.join(
            self.id,
            event_code,
            publication_id,
            text=text,
            filename=filename,
            file=file,
            sign=sign,
            attrs=attrs,
            include_attachment=include_attachment,
            reply_info=reply_info,
            multi=multi,
        )

    async def get_attachment(
        self, event_code: int, publication_id: int, attach_num: int = 1
    ) -> Response:
        """
        Get an attachment from a noticeboard item.

        :param event_code: The event code of the item.
        :param publication_id: The publication ID of the item.
        :param attach_num: The attachment number.
        """
        return await self.noticeboard.get_attachment(
            self.id, event_code, publication_id, attach_num
        )

    async def __aiter__(self):
        data = await self.noticeboard.all(self.id)

        for item in data["content"]["items"]:
            yield NoticeboardItem(
                self,
                item,
                (await self.__read(self.id, item["evtCode"], item["pubId"]))["content"][
                    "item"
                ]["text"],
            )
