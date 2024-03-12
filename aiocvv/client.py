import aiohttp
import shelve
import appdirs
import os
import asyncio
import json
from .core import CLIENT_USER_AGENT, CLIENT_DEV_APIKEY, CLIENT_CONTENT_TP
from .modules import *
from .errors import *
from datetime import datetime
from types import SimpleNamespace
from typing import Optional, Mapping, Any, Iterable, Union, Tuple
from aiohttp.client import (
    Fingerprint,
    ClientTimeout,
    SSLContext,  # to avoid checking if `ssl` module exists
)
from . import me
from .me import UserType, Teacher, Student, Parent
from aiohttp.helpers import sentinel
from aiohttp.typedefs import StrOrURL, LooseCookies, LooseHeaders
from urllib.parse import urljoin, urlsplit, urlparse
from typing_extensions import Self
from .types import Response
from .utils import find_exc

_json = json
LOGIN_METHODS = Union[Tuple[str, str], Tuple[str, str, str]]


class ClassevivaClient:
    """
    Client docs: https://web.spaggiari.eu/rest/v1/docs/html
                 https://web.spaggiari.eu/rest/v1/docs/plaintext

    The client class for Classeviva.
    `ClassevivaClient("yourusername", "yourpassword")`
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
        self._shelf_cache_path = os.path.join(appdirs.user_cache_dir(), "classeviva")
        self.__auth = AuthenticationModule(
            self
        )  # NOTE: keeping this private for obvious reasons
        self.__teachers = None
        self.__students = None
        self.__parents = None
        self.__users = None
        self.__me = None

    #          Modules          #
    # Using properties here so only the needed
    # modules will be initialized when needed.

    @property
    def teachers(self) -> TeachersModule:
        if self.__teachers is None:
            self.__teachers = TeachersModule(self)

        return self.__teachers

    @property
    def students(self) -> StudentsModule:
        if self.__students is None:
            self.__students = StudentsModule(self)

        return self.__students

    @property
    def parents(self) -> ParentsModule:
        if self.__parents is None:
            self.__parents = ParentsModule(self)

        return self.__parents

    @property
    def me(self) -> Optional[Union[Student, Parent, Teacher]]:
        return self.__me

    # HTTP requests and caching #
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
        """Make an HTTP request to the Classeviva REST APIs."""
        if urlsplit(str_or_url).scheme:
            raise ValueError(
                f"Invalid URL given: The URL provided is not for {self.BASE_URL}."
            )

        if not str_or_url.startswith(self.BASE_URL):
            str_or_url = urljoin(self.BASE_URL, str_or_url.lstrip("/"))

        login = await self.__auth.login(
            self.__username, self.__password, self.__identity
        )
        token = login["token"]

        parsed_url = urlparse(str_or_url)
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
                    str_or_url,
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
        try:
            data = await self.__auth.login(
                self.__username, self.__password, self.__identity
            )
        except AuthenticationError:
            if raise_exceptions:
                raise

            return False

        status = await self.__auth.status(data["token"])
        type = UserType(status["ident"][:1])

        # this is because parents doesn't have card, and
        # parents can request all of the students' endpoints
        carder = (
            self.students if type == UserType.parent else getattr(self, type.name + "s")
        )

        card = await carder.request(
            "GET", f'{"".join(filter(str.isdigit, status["ident"]))}/card'
        )
        cls = getattr(me, type.name.capitalize())
        self.__me = cls(self, **card["content"]["card"])
        return True

    async def __await_login(self) -> Self:
        await self.login()
        return self

    def __await__(self):
        return self.__await_login().__await__()
