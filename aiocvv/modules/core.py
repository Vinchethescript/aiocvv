"""
This module contains the base classes for the students, parents and teachers modules.
"""

import shelve
import os
from abc import ABC
from types import SimpleNamespace
from typing import Optional, Mapping, Any, Iterable, Union, IO, TYPE_CHECKING
from io import BytesIO, StringIO
from base64 import b64encode
from urllib.parse import urljoin
from aiohttp.client import (
    Fingerprint,
    ClientTimeout,
    SSLContext,
)
from aiohttp.helpers import sentinel
from aiohttp.typedefs import StrOrURL, LooseCookies, LooseHeaders
from ..types import Response


class Noticeboard:
    """
    Represents the noticeboard functionality in the ClasseViva API.
    """

    def __init__(self, module: "Module"):
        self.module = module

    @staticmethod
    def __get_flags(*args: bool):
        return "".join(str(int(arg)) for arg in args)

    async def all(self, id: int) -> Response:  # pylint: disable=redefined-builtin
        """
        Get all the noticeboard items.

        :param id: The ID of the student/teacher.

        :return: The response from the API.
        """

        return await self.module.request("GET", f"/{id}/noticeboard")

    async def read(
        self,
        id: int,  # pylint: disable=redefined-builtin
        event_code: int,
        publication_id: int,
        *,
        attrs: bool = True,
        include_attachment: bool = False,
        reply_info: bool = False,
        multi: bool = False,
    ) -> Response:
        """
        Read a noticeboard item.

        .. note::
            This will automatically mark the item as read from the Classeviva backend.

        :param id: The ID of the student/teacher.
        :param event_code: The code of the notice.
        :param publication_id: The ID itself of the notice.
        :param attrs: Optional. Whether to include attributes.
        :param include_attachment: Optional. Whether to include attachments.
        :param reply_info: Optional. Whether to include reply information.
        :param multi: Optional. Whether to get all of the attachments of the
                      item. This is useful when ``include_attachment`` is True.

        :return: The response from the API.
        """

        flags = self.__get_flags(attrs, include_attachment, reply_info)
        multi = "multi" if multi else ""
        return await self.module.request(
            "POST",
            f"/{id}/noticeboard/read{multi}/{event_code}/{publication_id}/{flags}",
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
        id: int,  # pylint: disable=redefined-builtin
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
        multi: bool = False,
    ) -> Response:
        """
        Join a noticeboard item.

        .. note::
            This will automatically mark the item as read from the Classeviva backend.

        :param id: The ID of the student/teacher.
        :param event_code: The code of the notice.
        :param publication_id: The ID itself of the notice.
        :param text: Optional. The text to join with.
        :param file: Optional. The file object to join with.
        :param filename: Optional. The name of the file to join with.
        :param sign: Optional. Whether to sign the join.
        :param attrs: Optional. Whether to include attributes.
        :param include_attachment: Optional. Whether to include attachments.
        :param reply_info: Optional. Whether to include reply information.
        :param multi: Optional. Whether to get all of the attachments of the
                      item. This is useful when ``include_attachment`` is True.


        :return: The response from the API.
        """

        flags, payload = await self.__pre_join(
            text=text,
            filename=filename,
            file=file,
            sign=sign,
            attrs=attrs,
            include_attachment=include_attachment,
            reply_info=reply_info,
        )
        multi = "multi" if multi else ""
        return await self.module.request(
            "POST",
            f"/{id}/noticeboard/read{multi}/{event_code}/{publication_id}/{flags}",
            json=payload,
        )

    async def get_attachment(
        self,
        id: int,  # pylint: disable=redefined-builtin
        event_code: int,
        publication_id: int,
        attach_num: int = 1,
    ) -> Response:
        """
        Get an attachment from a noticeboard item.

        :param id: The ID of the student/teacher.
        :param event_code: The code of the notice.
        :param publication_id: The ID itself of the notice.
        :param attach_num: Optional. The attachment number.

        :return: The response from the API.
        """

        return await self.module.request(
            "GET",
            f"/{id}/noticeboard/attach/{event_code}/{publication_id}/{attach_num}",
        )


class Module(ABC):
    """
    This is the base module for the students, parents and teachers modules.
    It implements the basic methods that are shared between the three modules.
    """

    endpoint = None

    def __init__(self, client):
        if not self.endpoint:
            raise ValueError("An endpoint must be added.")

        self.client = client

        if TYPE_CHECKING:
            from ..client import (
                ClassevivaClient,
            )  # pylint: disable=import-outside-toplevel

            self.client: ClassevivaClient = client

    def get_cache(self) -> shelve.Shelf:
        return shelve.open(
            self.client._shelf_cache_path  # pylint: disable=protected-access
        )

    async def request(
        self,
        method: str,
        endpoint: str,
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
        """
        Make a raw HTTP request to the Classeviva REST APIs using aiohttp.

        This function calls :meth:`ClassevivaClient.request` to make the
        request itself, the only difference is that the request will be
        forced to be inside the module.

        .. note::
            For example, if you want to make a request to
            the ``/students/<sid>/homeworks`` endpoint from the students module,
            the `endpoint` parameter should be ``/<sid>/homeworks``, otherwise
            the request will fail as it'll make a request to
            ``/students/students/<sid>/homeworks``, which is not valid.

        For information about the valid endpoints,
        refer to the Classeviva REST API documentation:

        * `HTML Documentation <https://web.spaggiari.eu/rest/v1/docs/html>`_
        * `Plaintext Documentation <https://web.spaggiari.eu/rest/v1/docs/plaintext>`_

        :param method: The HTTP method to use.
        :param endpoint: The path for the request. Must be a relative URL
                         since the base URL is `https://web.spaggiari.eu/rest/v1/<module>/`.
        :param params: Optional. The query parameters for the request.
        :param data: Optional. The request body data.
        :param json: Optional. The request body JSON data.
        :param cookies: Optional. The cookies to include in the request.
        :param headers: Optional. The headers to include in the request.
        :param skip_auto_headers: Optional. The headers to skip from automatic inclusion.
        :param compress: Optional. The compression method to use.
        :param chunked: Optional. Whether to use chunked transfer encoding.
        :param raise_for_status: Optional. Whether to raise an exception
                                 for non-successful responses.
        :param read_until_eof: Optional. Whether to read the response until EOF.
        :param proxy: Optional. The proxy URL or path.
        :param timeout: Optional. The request timeout.
        :param verify_ssl: Optional. Whether to verify SSL certificates.
        :param fingerprint: Optional. The SSL fingerprint.
        :param ssl_context: Optional. The SSL context.
        :param ssl: Optional. The SSL configuration.
        :param proxy_headers: Optional. The headers to include in the proxy request.
        :param trace_request_ctx: Optional. The request context for tracing.
        :param read_bufsize: Optional. The read buffer size.

        :type method: str
        :type endpoint: str
        :type params: Optional[Mapping[str, str]]
        :type data: Any
        :type json: dict
        :type cookies: Optional[LooseCookies]
        :type headers: Optional[LooseHeaders]
        :type skip_auto_headers: Optional[Iterable[str]]
        :type compress: Optional[str]
        :type chunked: Optional[bool]
        :type raise_for_status: bool
        :type read_until_eof: bool
        :type proxy: Optional[StrOrURL]
        :type timeout: ClientTimeout
        :type verify_ssl: Optional[bool]
        :type fingerprint: Optional[bytes]
        :type ssl_context: Optional[SSLContext]
        :type ssl: Optional[Union[SSLContext, bool, Fingerprint]]
        :type proxy_headers: Optional[LooseHeaders]
        :type trace_request_ctx: Optional[SimpleNamespace]
        :type read_bufsize: Optional[int]

        :return: The HTTP response dictionary.
        :rtype: dict
        """
        return await self.client.request(
            method,
            urljoin(
                self.endpoint.strip("/") + "/",
                endpoint.lstrip("/"),
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


class BaseModule(Module, ABC):
    """
    Base class for student and peacher modules.
    It's not the base class for the parent module because
    it has totally different endpoints, which is why
    parents can access all of the student's endpoints.
    """

    async def get_card(self, id: int) -> Response:  # pylint: disable=redefined-builtin
        """
        Get the card of the user.
        """
        return await self.request("GET", f"/{id}/card")

    @property
    def noticeboard(self) -> Noticeboard:
        """
        Get the noticeboard-related endpoints, which have
        been separated to avoid making too many functions
        in one class for the same endpoints.
        """
        return Noticeboard(self)
