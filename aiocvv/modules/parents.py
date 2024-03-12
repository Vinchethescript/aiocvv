from .core import Module
from ..types import Response, Date
from typing import Optional
from ..utils import convert_date


class ParentsTalks:
    """XXX: This hasn't been tested for obvious reasons."""

    def __init__(self, module: "ParentsModule"):
        self.module = module

    async def teachers(self, student_id: int) -> Response:
        return await self.module.request("GET", f"/{student_id}/talks/teachers")

    async def frames(
        self,
        student_id: int,
        teacher_id: int,
        start: Optional[Date] = None,
        end: Optional[Date] = None,
    ) -> Response:
        if start and end and end < start:
            raise ValueError("end must be greater than start")

        start = convert_date(start) if start else ""
        end = convert_date(end) if start else ""

        return await self.module.request(
            "GET",
            f"/{student_id}/talks/getframes/{teacher_id}/{start}/{end}".rstrip("/"),
        )

    async def all(
        self,
        student_id: int,
        start: Optional[Date] = None,
        end: Optional[Date] = None,
    ) -> Response:
        if start and end and end < start:
            raise ValueError("end must be greater than start")

        start = convert_date(start) if start else ""
        end = convert_date(end) if start else ""

        return await self.module.request(
            "GET", f"/{student_id}/talks/teachersframes2/{start}/{end}".rstrip("/")
        )

    async def book(
        self,
        student_id: int,
        teacher_id: int,
        frame_id: int,
        slot_bitmask: int,
        *,
        cellphone: Optional[str] = None,
        email: Optional[str] = None,
        other: Optional[str] = None,
    ) -> Response:
        return await self.module.request(
            "POST",
            f"/{student_id}/talks/book/{teacher_id}/{frame_id}/{slot_bitmask}",
            json={"cell": cellphone, "email": email, "altro": other},
        )

    async def booked(
        self,
        student_id: int,
        start: Optional[Date] = None,
        end: Optional[Date] = None,
    ) -> Response:
        if start and end and end < start:
            raise ValueError("end must be greater than start")

        start = convert_date(start) if start else ""
        end = convert_date(end) if start else ""

        return await self.module.request(
            "GET", f"/{student_id}/talks/mytalks/{start}/{end}".rstrip("/")
        )

    async def delete(self, student_id: int, talk_id: int) -> Response:
        return await self.module.request(
            "POST", f"/{student_id}/talks/delete/{talk_id}"
        )

    async def message(self, student_id: int, talk_id: int, message: str) -> Response:
        return await self.module.request(
            "POST", f"/{student_id}/talks/mymessage/{talk_id}", json={"myMsg": message}
        )

    async def read(self, student_id: int, talk_id: int, read: bool) -> Response:
        return await self.module.request(
            "POST",
            f"/{student_id}/talks/teachermessage/{talk_id}",
            json={"messageRead": read},
        )


class ParentsOverallTalks:
    """XXX: This hasn't been tested for obvious reasons."""

    def __init__(self, module: "ParentsModule"):
        self.module = module

    async def list(self, student_id: int) -> Response:
        return await self.module.request("GET", f"/{student_id}/overalltalks/list")

    async def frames(
        self, student_id: int, overalltalk_id: int, teacher_id: int
    ) -> Response:
        return await self.module.request(
            "GET", f"/{student_id}/overalltalks/getframes/{overalltalk_id}/{teacher_id}"
        )

    async def book(
        self,
        student_id: int,
        overalltalk_id: int,
        teacher_id: int,
        frame_id: int,
        slot_number: int,
    ) -> Response:
        return await self.module.request(
            "POST",
            f"/{student_id}/overalltalks/book/{overalltalk_id}/{teacher_id}/{frame_id}/{slot_number}",
        )

    async def delete(
        self, student_id: int, overalltalk_id: int, event_id: int
    ) -> Response:
        return await self.module.request(
            "DELETE", f"/{student_id}/overalltalks/delete/{overalltalk_id}/{event_id}"
        )


class ParentsPayments:
    """XXX: This hasn't been tested for obvious reasons."""

    def __init__(self, module: "ParentsModule"):
        self.module = module

    async def payments(self, student_id: int) -> Response:
        return await self.module.request("GET", f"/{student_id}/pagoonline/payments")

    async def download_file(self, student_id: int, attach_id: int) -> Response:
        return await self.module.request(
            "GET", f"/{student_id}/pagoonline/downloadfile/{attach_id}"
        )

    async def privacy(self, student_id: int) -> Response:
        return await self.module.request("GET", f"/{student_id}/pagoonline/getprivacy")

    async def download_file_privacy(self, student_id: int, file_id: int) -> Response:
        return await self.module.request(
            "POST", f"/{student_id}/pagoonline/downloadfileprivacy/{file_id}"
        )

    async def set_privacy(
        self,
        student_id: int,
        name: str,
        surname: str,
        fiscal_code: str,
        relationship: str,
        iban: str,
        flag_privacy: bool,
        flag_coord: bool,
    ) -> Response:
        return await self.module.request(
            "POST",
            f"/{student_id}/pagoonline/setprivacy",
            json={
                "name": name,
                "surname": surname,
                "fiscalCode": fiscal_code,
                "relationship": relationship,
                "iban": iban,
                "flagPrivacy": flag_privacy,
                "flagCoord": flag_coord,
            },
        )


class ParentsModule(Module):
    endpoint = "parents"

    @property
    def talks(self) -> ParentsTalks:
        return ParentsTalks(self)

    @property
    def overall_talks(self) -> ParentsOverallTalks:
        return ParentsOverallTalks(self)

    @property
    def payments(self) -> ParentsPayments:
        return ParentsPayments(self)
