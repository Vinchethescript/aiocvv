import bcrypt

from ..errors import AuthenticationError, MultiIdentFound
from .core import Module
from ..core import CLIENT_USER_AGENT, CLIENT_DEV_APIKEY, CLIENT_CONTENT_TP
from aiohttp import ClientSession, ClientResponseError
from datetime import datetime, timezone
from typing import Optional
from ..utils import find_exc
from urllib.parse import urljoin


class AuthenticationModule(Module):
    endpoint = "auth"

    async def login(
        self, username: str, password: str, identity: Optional[str] = None
    ) -> dict:
        with self.get_cache() as cache:
            if "salt" not in cache:
                cache["salt"] = bcrypt.gensalt()

            hashed_pw = bcrypt.hashpw(password.encode(), cache["salt"]).decode()
            if "logins" not in cache:
                cache["logins"] = {}

            cache_key = f"{username}:{hashed_pw}"
            login_cache = cache["logins"]
            if identity:
                cache_key += f":{identity}"

            if cache_key in login_cache:
                this = login_cache[cache_key]
                expires_at = datetime.fromisoformat(this["expire"])
                if expires_at > datetime.now(timezone.utc):
                    return this

            req = {"uid": username, "pass": password}
            if identity:
                req["ident"] = identity

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

    async def status(self, token: str):
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
