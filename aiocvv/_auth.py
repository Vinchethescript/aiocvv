"""
This is responsible for handling the authentication of the client.
It is used internally by the client and should not be used directly.
"""

from urllib.parse import urljoin
from datetime import datetime, timezone
from typing import Optional

import bcrypt

from aiohttp import ClientSession, ClientResponseError
from .errors import AuthenticationError, MultiIdentFound
from .modules.core import Module, Response
from .core import CLIENT_USER_AGENT, CLIENT_DEV_APIKEY, CLIENT_CONTENT_TP
from .utils import find_exc


class AuthenticationModule(Module):
    """
    This module is responsible for handling the authentication of the client.
    """

    endpoint = "auth"

    async def login(
        self, username: str, password: str, identity: Optional[str] = None
    ) -> dict:
        """
        Get a temporary token to use as authentication with the given username and password.

        It works by preparing caches for all the future requests and
        then sending a POST request to the Classeviva API to get a
        temporary token to use in requests.

        If a token is found cached and unexpired, that one will be used instead
        of requesting a new one. Otherwise, this function will request a new
        one, and cache it again for future requests.

        :param username: The user's username, or email or badge to authenticate with.
        :param password: The user's password.
        :param identity: The user's identity, in case multiple are found.
        :return: The direct response from the Classeviva API containing the token.
        """
        with self.get_cache() as cache:
            if "salt" not in cache:
                cache["salt"] = bcrypt.gensalt()

            # hash the password to cache it
            hashed_pw = bcrypt.hashpw(password.encode(), cache["salt"]).decode()
            if "logins" not in cache:
                cache["logins"] = {}

            cache_key = f"{username}:{hashed_pw}"
            login_cache = cache["logins"]
            if identity:
                cache_key += f":{identity}"

            # check in the cache for the token and its expiration
            if cache_key in login_cache:
                this = login_cache[cache_key]
                expires_at = datetime.fromisoformat(this["expire"])
                if expires_at > datetime.now(timezone.utc):
                    return this

            req = {"uid": username, "pass": password}
            if identity:
                req["ident"] = identity

            # do the actual request to get the token, if expired or not found
            async with ClientSession(loop=self.client.loop) as session:
                async with session.post(
                    urljoin(self.client.BASE_URL, "auth/login"),
                    headers={
                        "User-Agent": CLIENT_USER_AGENT,
                        "Z-Dev-Apikey": CLIENT_DEV_APIKEY,
                        "Content-Type": CLIENT_CONTENT_TP,
                    },
                    json=req,
                ) as resp:
                    content = await resp.json()
                    if resp.status == 422:
                        msg = {
                            "content": content,
                            "status": resp.status,
                            "status_reason": resp.reason,
                        }
                        raise find_exc(msg, AuthenticationError)

                    if "choices" in content and (
                        not identity
                        or identity not in [c["ident"] for c in content["choices"]]
                    ):
                        choices = " * " + "\n * ".join(
                            f"{c['ident']} ({c['name']})" for c in content["choices"]
                        )
                        msg = "Multiple identities have been found, but none has been specified"
                        if identity:
                            msg = "Could not find the requested identity"

                        raise MultiIdentFound(
                            f"{msg}. Possible choices are:\n{choices}"
                        )

                    try:
                        resp.raise_for_status()
                    except ClientResponseError as e:
                        raise AuthenticationError(content) from e

                    # cache response, will be re-cached as soon as the token expires
                    login_cache[cache_key] = content
                    cache["logins"] = login_cache
                    return content

    async def status(self, token: str) -> dict:
        """
        Get the status of the given token.
        This function is not used, but it is still available.

        :param token: The token to check the status of.
        :return: The direct response from the Classeviva API.
        """
        with self.get_cache() as cache:
            if "logins_status" not in cache:
                cache["logins_status"] = {}

            status = cache["logins_status"]
            if token in status:
                this = status[token]
                expires_at = datetime.fromisoformat(this["expire"])
                if expires_at > datetime.now(timezone.utc):
                    return this

            async with ClientSession(loop=self.client.loop) as session:
                async with session.get(
                    urljoin(self.client.BASE_URL, "auth/status"),
                    headers={
                        "User-Agent": CLIENT_USER_AGENT,
                        "Z-Dev-Apikey": CLIENT_DEV_APIKEY,
                        "Content-Type": CLIENT_CONTENT_TP,
                        "Z-Auth-Token": token,
                    },
                ) as resp:
                    resp.raise_for_status()
                    status[token] = (await resp.json())["status"]
                    cache["logins_status"] = status
                    return status[token]
