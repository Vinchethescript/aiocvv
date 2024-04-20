"""
This module contains the custom exceptions raised by the library.
"""


class ClassevivaError(Exception):
    """
    A HTTP error occurred while communicating with the Classeviva API.
    """

    status_code = None

    def __init__(self, response):
        desc = response
        if isinstance(response, dict):
            content = response["content"]
            self.error = content["error"]
            self.message = content.get("message", "")
            self.reason = response["status_reason"]
            desc = self.error + (f": {self.message}" if self.message else "")

            if self.status_code is None or self.status_code != response["status"]:
                self.status_code = response["status"]
                desc = f"{self.status_code} {self.reason}: {desc}"

        super().__init__(desc)


# Request errors
class BadRequest(ClassevivaError):
    """
    The server returned a 4xx/500 status code.
    """

    status_code = 400


class Unauthorized(BadRequest):
    """
    The server returned a 401 status code.
    This is common when you try to make HTTP requests without an API key, or with an invalid one.
    """

    status_code = 401


class NotFound(BadRequest):
    """
    The server returned a 404 status code, meaning the requested resource doesn't exist.
    """

    status_code = 404


class UnprocessableEntity(BadRequest):
    """
    The server returned a 422 status code, meaning the request
    was well-formed but the server was unable to process it for some reason.

    This is common when you try to log in with wrong credentials.
    """

    status_code = 422


class TooManyRequests(BadRequest):
    """
    The server returned a 429 status code, meaning you've reached the rate limit.
    If you get this error, you should really wait some time before trying again.
    """

    status_code = 429


# Server errors
class InternalServerError(ClassevivaError):
    """
    The server returned a 500/5xx status code.
    """

    status_code = 500


class ServiceUnavailable(InternalServerError):
    """
    The server returned a 503 status code, meaning the requested resource is currently unavailable.
    """

    status_code = 503


# Authentication errors
class AuthenticationError(ClassevivaError):
    """
    An error occurred while trying to authenticate with the Classeviva API.
    """

    status_code = 422


class WrongCredentials(AuthenticationError):
    """
    You provided wrong credentials to the Classeviva API.
    """


class PasswordExpired(AuthenticationError):
    """
    You provided correct credentials to the Classeviva API, but your password has expired.
    This means you must renew it from the Classeviva website before you can use the API.
    """


class NoIdentAvailable(AuthenticationError):
    """
    You successfully logged in through email or nickname, but
    no valid accounts were found in the associated portfolio.
    """


class MultiIdentFound(AuthenticationError):
    """
    You successfully logged in through email or nickname, but
    multiple accounts were found in the associated portfolio.

    You should pass the specific identity to use as the `ident` parameter
    in the :class:`~aiocvv.client.ClassevivaClient` constructor.
    """
