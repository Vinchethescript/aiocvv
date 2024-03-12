from ..modules.core import TSCommonModule, Noticeboard
from typing import Optional, Any, IO, List
from io import BytesIO
from ..types import Response
from ..files import File


class Attachment(File):
    def __init__(self, item: "NoticeboardItem", data: dict):
        self.filename = data["fileName"]
        self.num = data["attachNum"]
        self.__item = item

    async def download(self):
        resp = await self.__item.noticeboard.get_attachment(
            self.__item.code, self.__item.id, self.num
        )
        data = BytesIO(resp["content"])
        super().__init__(data, self.filename)
        return self


class NoticeboardItem:
    def __init__(self, nb: "MyNoticeboard", payload: dict, content: str):
        self.__payload = payload
        self.__content = content
        self.__board = nb
        self.__attachments = []

    @property
    def noticeboard(self):
        return self.__board

    @property
    def content(self):
        return self.__content

    @property
    def id(self) -> int:
        return self.__payload["pubId"]

    @property
    def read(self):
        return self.__payload["readStatus"]

    @property
    def code(self) -> str:
        return self.__payload["evtCode"]

    @property
    def title(self) -> str:
        return self.__payload["cntTitle"]

    @property
    def category(self) -> str:
        return self.__payload["cntCategory"]

    @property
    def has_changed(self) -> bool:
        return self.__payload["cntHasChanged"]

    @property
    def attachments(self):
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
        except Exception:
            if raise_exc:
                raise

            return False

        return True


class MyNoticeboard(Noticeboard):
    def __init__(self, id: int, module: "TSCommonModule"):
        self.id = id
        super().__init__(module)
        self.__read = super().read

    async def all(self) -> List[NoticeboardItem]:
        ret = []
        async for item in self:
            ret.append(item)
        return ret

    async def __get(self, code: str, id: int) -> Response:
        items = await super().all(self.id)
        for item in items["content"]["items"]:
            if id == item["pubId"] and code == item["evtCode"]:
                return item

    async def read(self, event_code: str, publication_id: int) -> Response:
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
    ) -> Response:
        return await super().join(
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
        )

    async def get_attachment(
        self, event_code: int, publication_id: int, attach_num: int = 1
    ) -> Response:
        return await super().get_attachment(
            self.id, event_code, publication_id, attach_num
        )

    async def read_multi(
        self,
        event_code: str,
        publication_id: int,
        *,
        attrs: bool = True,
        include_attachment: bool = False,
        reply_info: bool = False,
    ) -> Response:
        return await super().read_multi(
            self.id,
            event_code,
            publication_id,
            attrs=attrs,
            include_attachment=include_attachment,
            reply_info=reply_info,
        )

    async def join_multi(
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
    ) -> Response:
        return await super().join_multi(
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
        )

    async def __aiter__(self):
        data = await super().all(self.id)
        if data["status"] < 200 or data["status"] >= 300:
            raise Exception(f"{data['status']} {data['status_reason']}")

        for item in data["content"]["items"]:
            yield NoticeboardItem(
                self,
                item,
                (await self.__read(self.id, item["evtCode"], item["pubId"]))["content"][
                    "item"
                ]["text"],
            )
