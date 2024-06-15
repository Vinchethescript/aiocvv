"""
This helper contains the classes that represent the noticeboard and its items.
The noticeboard can be used both by students and teachers.
"""

# pylint: disable=arguments-differ

from typing import Optional, Any, IO, List, Union
from io import BytesIO
from ..modules.core import BaseModule, Noticeboard
from ..types import Response
from ..errors import ClassevivaError


class File:
    """
    Represents a file to upload to the noticeboard when joining an item.

    This class is used as an argument for :meth:`~aiocvv.helpers.noticeboard.NoticeboardItem.join`.
    """

    def __init__(self, data: IO[Any], filename: str):
        data.seek(0)
        self.__data = data
        self.filename = filename

    @property
    def data(self) -> IO[Any]:
        """The file's data."""
        return self.__data

    def __str__(self):
        return self.filename

    def __repr__(self):
        return f"<File name={self.filename!r}>"


class PartialAttachment:
    """
    Represents an attachment of an uploaded noticeboard item.

    .. note::
        This comes from a *partial* item, so the attachment is not downloadable.
        To download the attachment, you must :func:`~aiocvv.helpers.noticeboard.PartialNoticeboardItem.read` the item first.
    """

    def __init__(self, data: dict):
        # pylint: disable=super-init-not-called
        self.filename = data["fileName"]
        self.num = data["attachNum"]


class Attachment(File, PartialAttachment):
    """
    Represents an attachment of an uploaded noticeboard item.
    """

    def __init__(self, item: "NoticeboardItem", data: dict):
        PartialAttachment.__init__(self, data)
        self.__item = item

    async def download(self):
        """Download the attachment."""
        resp = await self.__item.noticeboard.noticeboard.get_attachment(
            self.__item.noticeboard.id, self.__item.code, self.__item.id, self.num
        )
        data = BytesIO(resp["content"])
        super().__init__(data, self.filename)
        return self


class PartialNoticeboardItem:
    """
    Represents a item in the noticeboard *partially*.

    .. note::
        This class is *partial*, which means it must be :func:`~aiocvv.helpers.noticeboard.PartialNoticeboardItem.read` to get its content.
        This is because reading the item would change its read status.
    """

    def __init__(self, nb: "MyNoticeboard", payload: dict):
        self.__payload = payload
        self.__board = nb
        self.__attachments = []

    @property
    def noticeboard(self):
        """The noticeboard this item belongs to."""
        return self.__board

    @property
    def id(self) -> int:
        """The item's publication ID."""
        return self.__payload["pubId"]

    @property
    def is_read(self):
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
                if isinstance(self, NoticeboardItem):
                    self.__attachments.append(Attachment(self, attach))
                else:
                    self.__attachments.append(PartialAttachment(attach))

            self.__attachments = list(sorted(self.__attachments, key=lambda x: x.num))

        return self.__attachments

    async def read(self) -> Response:
        """
        Read the item.

        :return: The noticeboard full item.
        """
        return await self.__board.read(self.code, self.id)


class NoticeboardItem(PartialNoticeboardItem):
    """
    Represents a item in the noticeboard. See also :class:`~aiocvv.helpers.noticeboard.PartialNoticeboardItem`.
    """

    def __init__(self, nb: "MyNoticeboard", payload: dict, content: str):
        super().__init__(nb, payload)
        self.__content = content

    @property
    def content(self):
        """The item's content."""
        return self.__content

    async def read(self):
        """
        This function doesn't do anything, but exists for compatibility with partial items and to avoid useless requests.

        See also :func:`~aiocvv.helpers.noticeboard.PartialNoticeboardItem.read`.
        :return: This item.
        """
        return self

    async def join(
        self,
        text: Optional[str] = None,
        sign: Optional[bool] = None,
        file: Optional[File] = None,
        *,
        raise_exc: bool = True,
    ) -> bool:
        """
        Join this item.

        :param text: The text to send.
        :param sign: Whether to sign the text.
        :param file: The file to upload.
        :param raise_exc: Whether to raise an exception if an error occurs.

        :return: Whether the operation was successful.
        """
        try:
            await self.__board.noticeboard.join(
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


AnyNoticeboardItem = Union[PartialNoticeboardItem, NoticeboardItem]


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

    async def all(self) -> List[AnyNoticeboardItem]:
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

    async def get(
        self, code: str, id: int  # pylint: disable=redefined-builtin
    ) -> AnyNoticeboardItem:
        """
        Get a noticeboard item.

        .. note::
            The returned item may be *partial*, meaning that it doesn't contain some data.
            This is because you have to read the item to get the rest of the data, and that would change the read status of the item.

        :param code: The event code of the item.
        :param id: The publication ID of the item.

        :return: The partial noticeboard item.
        """

        payload = await self.__get(code, id)
        if payload["readStatus"]:
            return await self.read(code, id)

        return PartialNoticeboardItem(self, payload)

    async def read(self, event_code: str, publication_id: int) -> NoticeboardItem:
        """
        Read a noticeboard item.

        .. note::
            This will automatically mark the item as read from the Classeviva backend.

        :param event_code: The event code of the item.
        :param publication_id: The publication ID of the item.

        :return: The noticeboard full item.
        """
        data = await self.__read(self.id, event_code, publication_id)
        payload = await self.__get(event_code, publication_id)

        return NoticeboardItem(self, payload, data["content"]["item"]["text"])

    async def __aiter__(self):
        data = await self.noticeboard.all(self.id)

        for item in data["content"]["items"]:
            # return the full item if it's already been read
            if item["readStatus"]:
                yield NoticeboardItem(
                    self,
                    item,
                    (await self.__read(self.id, item["evtCode"], item["pubId"]))[
                        "content"
                    ]["item"]["text"],
                )
            else:
                yield PartialNoticeboardItem(
                    self,
                    item,
                )
