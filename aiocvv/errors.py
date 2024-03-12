class ClassevivaError(Exception):
    status_code = None

    def __init__(self, response):
        desc = response
        if isinstance(response, dict):
            content = response["content"]
            self.error = content["error"]
            self.message = content.get("message", "")
            self.reason = response["status_reason"]
            desc = self.error + (f": {self.message}" if self.message else "")

            if self.status_code == None or self.status_code != response["status"]:
                self.status_code = response["status"]
                desc = f"{self.status_code} {self.reason}: {desc}"

        super().__init__(desc)


# Request errors
class BadRequest(ClassevivaError):
    status_code = 400


class Unauthorized(BadRequest):
    status_code = 401


class NotFound(BadRequest):
    status_code = 404


class UnprocessableEntity(BadRequest):
    status_code = 422


class TooManyRequests(BadRequest):
    status_code = 429


# Server errors
class InternalServerError(ClassevivaError):
    status_code = 500


class ServiceUnavailable(InternalServerError):
    status_code = 503


# Authentication errors
class AuthenticationError(ClassevivaError):
    status_code = 422


class WrongCredentials(AuthenticationError):
    pass


class PasswordExpired(AuthenticationError):
    pass


class NoIdentAvailable(AuthenticationError):
    pass


class MultiIdentFound(AuthenticationError):
    pass
