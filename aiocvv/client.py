"""The module where the ClassevivaClient class is located."""

import shelve
import os
import asyncio
import json
from datetime import datetime
from types import SimpleNamespace
from typing import Optional, Mapping, Any, Iterable, Union, Tuple
from urllib.parse import urljoin, urlsplit, urlparse

import aiohttp
from appdirs import user_cache_dir
from typing_extensions import Self
from aiohttp.client import (
    Fingerprint,
    ClientTimeout,
    SSLContext,  # to avoid checking if `ssl` module exists
)
from aiohttp.helpers import sentinel
from aiohttp.typedefs import StrOrURL, LooseCookies, LooseHeaders
from .core import CLIENT_USER_AGENT, CLIENT_DEV_APIKEY, CLIENT_CONTENT_TP
from .modules import (
    TeachersModule,
    StudentsModule,
    ParentsModule,
)
from . import me
from .errors import AuthenticationError
from .me import UserType, Teacher, Student, Parent
from .types import Response
from .utils import find_exc
from ._auth import AuthenticationModule

_json = json
LoginMethods = Union[Tuple[str, str], Tuple[str, str, str]]


class ClassevivaClient:
    """
    The client class for Classeviva.

    This class provides an interface to interact with the Classeviva REST APIs,
    where all the requests from this module are made.
    You can get any information from Classeviva by either using the :attr:`me` attribute
    or by making manual requests using the appropriate module or the :meth:`request` method-

    The modules are used to make manual HTTP requests to the Classeviva APIs.
    This is useful when:

    * You use the :attr:`me` attribute to automatically get the information you need, which chooses the correct module to use;
    * You want to make a request to an endpoint that is not (yet) or partially implemented in this wrapper;
    * You want to have more control over the request or response.
    * You don't want to manually write every URL, like you would do with the :meth:`request` method.

    .. note::
        Of course, if you decide to use modules,
        you will have to parse the response yourself,
        as they only return the raw response.


    For more information about the endpoints,
    refer to the Classeviva REST API documentation:

    * `HTML Documentation <https://web.spaggiari.eu/rest/v1/docs/html>`_
    * `Plaintext Documentation <https://web.spaggiari.eu/rest/v1/docs/plaintext>`_


    :param username: The username for authentication.
    :param password: The password for authentication.
    :param identity: Optional. The identity for authentication.
    :param loop: Optional. The event loop to use.
                 If not provided, the default event loop will be used.

    :type username: str
    :type password: str
    :type identity: str
    :type loop: asyncio.AbstractEventLoop
    """

    BASE_URL = "https://web.spaggiari.eu/rest/v1/"
    PARSED_BASE = urlparse(BASE_URL)

    def __init__(
        self,
        username: str,
        password: str,
        identity: Optional[str] = None,
        *,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ):
        self.loop = loop or asyncio.get_event_loop()
        self.__username = username
        self.__password = password
        self.__identity = identity
        self._shelf_cache_path = os.path.join(user_cache_dir(), "classeviva")
        self.__auth = AuthenticationModule(
            self
        )  # NOTE: keeping this private for obvious reasons
        self.__teachers = None
        self.__students = None
        self.__parents = None
        self.__me = None

    #          Modules          #
    # Using properties here so only the needed
    # modules will be initialized when needed.

    @property
    def teachers(self) -> TeachersModule:
        """
        Get the teachers module for manually making
        requests to the teachers' endpoints.

        .. warning::
            This whole module has not been implemented yet, because it's
            not possible to test it without having a teacher account.
            Therefore, this is just a placeholder for future updates, which
            means there are no endpoints in here. If you are a teacher and
            you want to contribute to this project, feel free to open a pull request.
            Otherwise, you'll have to manually make requests using the :meth:`request` method.

        :return: The (empty) module instance.
        """
        if self.__teachers is None:
            self.__teachers = TeachersModule(self)

        return self.__teachers

    @property
    def students(self) -> StudentsModule:
        """
        Get the students module for manually making
        requests to the students' endpoints.

        :return: The module instance.
        """
        if self.__students is None:
            self.__students = StudentsModule(self)

        return self.__students

    @property
    def parents(self) -> ParentsModule:
        """
        Get the parents module for manually making
        requests to the parents' endpoints.

        :return: The module instance.
        """
        if self.__parents is None:
            self.__parents = ParentsModule(self)

        return self.__parents

    @property
    def me(self) -> Optional[Union[Student, Parent, Teacher]]:
        """
        Get the current user.

        .. note::
            This will be None until :meth:`login` is called or the class is awaited.

        :return: The current user instance.
        """
        return self.__me

    async def request(
        self,
        method: str,
        endpoint: str,
        *,
        params: Optional[Mapping[str, str]] = None,
        data: Any = None,
        json: Optional[dict] = None,  # pylint: disable=redefined-outer-name
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

        For information about the valid endpoints,
        refer to the Classeviva REST API documentation:

        * `HTML Documentation <https://web.spaggiari.eu/rest/v1/docs/html>`_
        * `Plaintext Documentation <https://web.spaggiari.eu/rest/v1/docs/plaintext>`_

        :param method: The HTTP method to use.
        :param endpoint: The path for the request.
                         Must be a relative URL since the base URL is `https://web.spaggiari.eu/rest/v1/`.
        :param params: Optional. The query parameters for the request.
        :param data: Optional. The request body data.
        :param json: Optional. The request body JSON data.
        :param cookies: Optional. The cookies to include in the request.
        :param headers: Optional. The headers to include in the request.
        :param skip_auto_headers: Optional. The headers to skip from automatic inclusion.
        :param compress: Optional. The compression method to use.
        :param chunked: Optional. Whether to use chunked transfer encoding.
        :param raise_for_status: Optional. Whether to raise an exception for non-successful responses.
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
        """
        if urlsplit(endpoint).scheme:
            raise ValueError(
                f"Invalid URL given: The URL provided is not for {self.BASE_URL}."
            )

        if not endpoint.startswith(self.BASE_URL):
            endpoint = urljoin(self.BASE_URL, endpoint.lstrip("/"))

        login = await self.__auth.login(
            self.__username, self.__password, self.__identity
        )
        token = login["token"]

        parsed_url = urlparse(endpoint)
        cache = await self.loop.run_in_executor(
            None, shelve.open, self._shelf_cache_path
        )
        if "requests" not in cache:
            cache["requests"] = {}

        reqs_cache = cache["requests"]
        part = parsed_url.path[len(self.PARSED_BASE.path) :]

        try:
            _headers = {
                "User-Agent": CLIENT_USER_AGENT,
                "Z-Dev-Apikey": CLIENT_DEV_APIKEY,
                "Content-Type": CLIENT_CONTENT_TP,
                "Z-Auth-Token": token,
            }

            if headers:
                headers.update(_headers)
            else:
                headers = _headers

            if part in reqs_cache:
                headers["If-None-Match"] = reqs_cache[part]["etag"]
                old_req_headers = reqs_cache[part]["headers"]
                headers_lower = {k.lower(): v for k, v in old_req_headers.items()}
                if "z-cache-control" in headers_lower:
                    for val in headers_lower["z-cache-control"].split(","):
                        k, v = val.strip().split("=")
                        if k.strip() == "max-age":
                            expires_at = datetime.fromtimestamp(
                                reqs_cache[part]["created_at"] + int(v.strip(" ;"))
                            )
                            if expires_at > datetime.now():
                                resp = reqs_cache[part]
                                if raise_for_status and (
                                    resp["status"] < 200 or resp["status"] >= 300
                                ):
                                    raise find_exc(resp)

                                return resp

            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method,
                    endpoint,
                    params=params,
                    data=data,
                    json=json,
                    cookies=cookies,
                    headers=headers,
                    skip_auto_headers=skip_auto_headers,
                    compress=compress,
                    chunked=chunked,
                    raise_for_status=False,
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
                ) as resp:
                    if resp.status == 304:
                        return reqs_cache[part]

                    read_data = await resp.content.read()
                    content = read_data

                    try:
                        content = _json.loads(content)
                    except (_json.JSONDecodeError, UnicodeDecodeError) as e:
                        # this is not JSON
                        if not isinstance(e, UnicodeDecodeError):
                            content = read_data.decode()

                    etag = resp.headers.get("ETag")
                    ret = {
                        "created_at": datetime.now().timestamp(),
                        "content": content,
                        "headers": dict(resp.headers),
                        "status": resp.status,
                        "status_reason": resp.reason,
                    }
                    if etag:
                        ret["etag"] = etag
                        reqs_cache[part] = ret

                    if raise_for_status and (resp.status < 200 or resp.status >= 300):
                        raise find_exc(ret)

                    return ret
        finally:
            cache["requests"] = reqs_cache
            await self.loop.run_in_executor(None, cache.close)

    async def login(self, raise_exceptions: bool = True):
        """
        Log in to Classeviva using the passed credentials.

        :param raise_exceptions: Optional. Whether to raise exceptions for authentication errors.
        :type raise_exceptions: bool

        :return: True if login is successful, False otherwise.
        :rtype: bool
        """
        try:
            data = await self.__auth.login(
                self.__username, self.__password, self.__identity
            )
        except AuthenticationError:
            if raise_exceptions:
                raise

            return False

        status = await self.__auth.status(data["token"])
        utype = UserType(status["ident"][:1])

        # this is because parents doesn't have card, and
        # parents can request all of the students' endpoints
        carder = (
            self.students
            if utype == UserType.parent
            else getattr(self, utype.name + "s")
        )

        card = await carder.request(
            "GET", f'{"".join(filter(str.isdigit, status["ident"]))}/card'
        )
        cls = getattr(me, utype.name.capitalize())
        self.__me = cls(self, **card["content"]["card"])
        return True

    async def __await_login(self) -> Self:
        await self.login()
        return self

    def __await__(self):
        return self.__await_login().__await__()
