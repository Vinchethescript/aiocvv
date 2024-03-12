import shelve
import os
from abc import ABC
from types import SimpleNamespace
from typing import Optional, Mapping, Any, Iterable, Union, IO
from aiohttp.client import (
    Fingerprint,
    ClientTimeout,
    SSLContext,
)
from aiohttp.helpers import sentinel
from aiohttp.typedefs import StrOrURL, LooseCookies, LooseHeaders
from urllib.parse import urljoin
from ..types import Response
from io import BytesIO, StringIO
from base64 import b64encode


class Noticeboard:
    def __init__(self, module: "Module"):
        self.module = module

    @staticmethod
    def __get_flags(*args: bool):
        return "".join(str(int(arg)) for arg in args)

    # def __call__(self, id: int) -> "ContextNoticeboard":
    #    return ContextNoticeboard(id, self.module)

    async def all(self, id: int) -> Response:
        return await self.module.request("GET", f"/{id}/noticeboard")

    async def read(
        self,
        id: int,
        event_code: int,
        publication_id: int,
        *,
        attrs: bool = True,
        include_attachment: bool = False,
        reply_info: bool = False,
    ) -> Response:
        flags = self.__get_flags(attrs, include_attachment, reply_info)
        return await self.module.request(
            "POST",
            f"/{id}/noticeboard/read/{event_code}/{publication_id}/{flags}",
            json={"join": False},
        )

    async def __pre_join(
        self,
        *,
        text: Optional[str] = None,
        filename: Optional[str] = None,
        file: Optional[IO[Any]] = None,
        sign: Optional[bool] = None,
        attrs: bool = True,
        include_attachment: bool = False,
        reply_info: bool = False,
    ):
        flags = self.__get_flags(attrs, include_attachment, reply_info)
        payload = {"join": True}
        if text:
            payload["text"] = text

        if file:
            if isinstance(file, (BytesIO, StringIO)):
                cont = file.getvalue()
            else:
                cont = file.read()

            if not filename and not file.name:
                raise ValueError("a file name must be specified")

            payload["file"] = await self.module.client.loop.run_in_executor(
                None, lambda: b64encode(cont).decode("utf-8")
            )
            payload["filename"] = os.path.basename(
                getattr(file, "name", None) or filename
            )

        if sign:
            payload["sign"] = sign

        return flags, payload

    async def join(
        self,
        id: int,
        event_code: int,
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
        flags, payload = await self.__pre_join(
            text=text,
            filename=filename,
            file=file,
            sign=sign,
            attrs=attrs,
            include_attachment=include_attachment,
            reply_info=reply_info,
        )
        return await self.module.request(
            "POST",
            f"/{id}/noticeboard/read/{event_code}/{publication_id}/{flags}",
            json=payload,
        )

    async def get_attachment(
        self, id: int, event_code: int, publication_id: int, attach_num: int = 1
    ) -> Response:
        return await self.module.request(
            "GET",
            f"/{id}/noticeboard/attach/{event_code}/{publication_id}/{attach_num}",
        )

    async def read_multi(
        self,
        id: int,
        event_code: int,
        publication_id: int,
        *,
        attrs: bool = True,
        include_attachment: bool = False,
        reply_info: bool = False,
    ) -> Response:
        flags = self.__get_flags(attrs, include_attachment, reply_info)
        return await self.module.request(
            "POST",
            f"/{id}/noticeboard/readmulti/{event_code}/{publication_id}/{flags}",
            json={"join": False},
        )

    async def join_multi(
        self,
        id: int,
        event_code: int,
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
        flags, payload = await self.__pre_join(
            text=text,
            filename=filename,
            file=file,
            sign=sign,
            attrs=attrs,
            include_attachment=include_attachment,
            reply_info=reply_info,
        )

        return await self.module.request(
            "POST",
            f"/{id}/noticeboard/readmulti/{event_code}/{publication_id}/{flags}",
            payload,
        )


class Module(ABC):
    endpoint = None

    def __init__(self, client):
        if not self.endpoint:
            raise ValueError("An endpoint must be added.")
        from ..client import ClassevivaClient

        self.client: ClassevivaClient = client

    def get_cache(self):
        return shelve.open(self.client._shelf_cache_path)

    async def request(
        self,
        method: str,
        str_or_url: StrOrURL,
        *,
        params: Optional[Mapping[str, str]] = None,
        data: Any = None,
        json: Any = None,
        cookies: Optional[LooseCookies] = None,
        headers: Optional[LooseHeaders] = None,
        skip_auto_headers: Optional[Iterable[str]] = None,
        compress: Optional[str] = None,
        chunked: Optional[bool] = None,
        raise_for_status: bool = True,
        read_until_eof: bool = True,
        proxy: Optional[StrOrURL] = None,
        timeout: Union[ClientTimeout, object] = sentinel,
        verify_ssl: Optional[bool] = None,
        fingerprint: Optional[bytes] = None,
        ssl_context: Optional[SSLContext] = None,
        ssl: Optional[Union[SSLContext, bool, Fingerprint]] = None,
        proxy_headers: Optional[LooseHeaders] = None,
        trace_request_ctx: Optional[SimpleNamespace] = None,
        read_bufsize: Optional[int] = None,
    ) -> Response:
        return await self.client.request(
            method,
            urljoin(
                self.endpoint.strip("/") + "/",
                str_or_url.lstrip("/"),
            ),
            params=params,
            data=data,
            json=json,
            cookies=cookies,
            headers=headers,
            skip_auto_headers=skip_auto_headers,
            compress=compress,
            chunked=chunked,
            raise_for_status=raise_for_status,
            read_until_eof=read_until_eof,
            proxy=proxy,
            timeout=timeout,
            verify_ssl=verify_ssl,
            fingerprint=fingerprint,
            ssl_context=ssl_context,
            ssl=ssl,
            proxy_headers=proxy_headers,
            trace_request_ctx=trace_request_ctx,
            read_bufsize=read_bufsize,
        )


class TSCommonModule(Module):
    """
    Base class for Student and Teacher modules.
    It's not the base class for Parent because
    it has totally different endpoints, and it
    can access all of the Student endpoints.
    """

    async def get_card(self, id: int):
        return await self.request("GET", f"/{id}/card")

    @property
    def noticeboard(self):
        return Noticeboard(self)
