"""
This module is used to make HTTP requests to the parents endpoint.
It can only be used by parents, and not by students.
"""

from typing import Optional
from .core import Module
from ..types import Response, Date
from ..utils import convert_date


class ParentsTalks:
    """
    This class provides endpoints to interact with the parents' talks API.
    """

    def __init__(self, module: "ParentsModule"):
        self.module = module

    async def teachers(self, student_id: int) -> Response:
        """
        Get the list of teachers for a specific student.

        :param student_id: The ID of the student.
        :return: The response from the Classeviva API.
        :rtype: dict
        """
        return await self.module.request("GET", f"/{student_id}/talks/teachers")

    async def frames(
        self,
        student_id: int,
        teacher_id: int,
        start: Optional[Date] = None,
        end: Optional[Date] = None,
    ) -> Response:
        """
        Get the frames for a specific student and teacher within a given time range.

        :param student_id: The ID of the student.
        :param teacher_id: The ID of the teacher.
        :param start: Optional. The start date of the time range.
        :param end: Optional. The end date of the time range.
        :return: The response from the Classeviva API.
        :rtype: dict
        :raises ValueError: If the end date is earlier than the start date.
        """
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
        """
        Get all the frames for a specific student within a given time range.

        :param student_id: The ID of the student.
        :param start: Optional. The start date of the time range.
        :param end: Optional. The end date of the time range.
        :return: The response from the Classeviva API.
        :rtype: dict
        :raises ValueError: If the end date is earlier than the start date.
        """
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
        """
        Book a frame for a specific student with the given details.

        :param student_id: The ID of the student.
        :param teacher_id: The ID of the teacher.
        :param frame_id: The ID of the frame.
        :param slot_bitmask: The bitmask for the time slots.
        :param cellphone: Optional. The cellphone number.
        :param email: Optional. The email address.
        :param other: Optinoal. Other details.
        :return: The response from the Classeviva API.
        :rtype: dict
        """
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
        """
        Get the booked frames for a specific student within a given time range.

        :param student_id: The ID of the student.
        :param start: Optional. The start date of the time range.
        :param end: Optional. The end date of the time range.
        :return: The response from the Classeviva API.
        :rtype: dict
        :raises ValueError: If the end date is earlier than the start date.
        """
        if start and end and end < start:
            raise ValueError("end must be greater than start")

        start = convert_date(start) if start else ""
        end = convert_date(end) if start else ""

        return await self.module.request(
            "GET", f"/{student_id}/talks/mytalks/{start}/{end}".rstrip("/")
        )

    async def delete(self, student_id: int, talk_id: int) -> Response:
        """
        Delete a specific talk for a student.

        :param student_id: The ID of the student.
        :param talk_id: The ID of the talk.
        :return: The response from the Classeviva API.
        :rtype: dict
        """
        return await self.module.request(
            "POST", f"/{student_id}/talks/delete/{talk_id}"
        )

    async def message(self, student_id: int, talk_id: int, message: str) -> Response:
        """
        Send a message for a specific talk.

        :param student_id: The ID of the student.
        :param talk_id: The ID of the talk.
        :param message: The message to send.
        :return: The response from the Classeviva API.
        :rtype: dict
        """
        return await self.module.request(
            "POST", f"/{student_id}/talks/mymessage/{talk_id}", json={"myMsg": message}
        )

    async def read(self, student_id: int, talk_id: int, read: bool) -> Response:
        """
        Mark a specific talk as read or unread.

        :param student_id: The ID of the student.
        :param talk_id: The ID of the talk.
        :param read: Whether to mark the talk as read or unread.
        :return: The response from the Classeviva API.
        :rtype: dict
        """
        return await self.module.request(
            "POST",
            f"/{student_id}/talks/teachermessage/{talk_id}",
            json={"messageRead": read},
        )


class ParentsOverallTalks:
    """
    Represents a class for managing overall talks for parents.
    """

    def __init__(self, module: "ParentsModule"):
        self.module = module

    async def list(self, student_id: int) -> Response:
        """
        Get the list of overall talks for a specific student.

        :param student_id: The ID of the student.
        :return: The response from the Classeviva API.
        :rtype: dict
        """
        return await self.module.request("GET", f"/{student_id}/overalltalks/list")

    async def frames(
        self, student_id: int, overalltalk_id: int, teacher_id: int
    ) -> Response:
        """
        Get the frames for a specific overall talk.

        :param student_id: The ID of the student.
        :param overalltalk_id: The ID of the overall talk.
        :param teacher_id: The ID of the teacher.
        :return: The response from the Classeviva API.
        :rtype: dict
        """
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
        """
        Book a slot for a specific overall talk.

        :param student_id: The ID of the student.
        :param overalltalk_id: The ID of the overall talk.
        :param teacher_id: The ID of the teacher.
        :param frame_id: The ID of the frame.
        :param slot_number: The slot number.
        :return: The response from the Classeviva API.
        :rtype: dict
        """
        return await self.module.request(
            "POST",
            f"/{student_id}/overalltalks/book/{overalltalk_id}"
            f"/{teacher_id}/{frame_id}/{slot_number}",
        )

    async def delete(
        self, student_id: int, overalltalk_id: int, event_id: int
    ) -> Response:
        """
        Delete a specific overall talk event.

        :param student_id: The ID of the student.
        :param overalltalk_id: The ID of the overall talk.
        :param event_id: The ID of the event.
        :return: The response from the Classeviva API.
        :rtype: dict
        """
        return await self.module.request(
            "DELETE", f"/{student_id}/overalltalks/delete/{overalltalk_id}/{event_id}"
        )


class ParentsPayments:
    """
    This class provides endpoints for handling parents' payments.
    """

    def __init__(self, module: "ParentsModule"):
        self.module = module

    async def payments(self, student_id: int) -> Response:
        """
        Get the payments for a specific student.

        :param student_id: The ID of the student.
        :return: The response from the Classeviva API.
        :rtype: dict
        """
        return await self.module.request("GET", f"/{student_id}/pagoonline/payments")

    async def download_file(self, student_id: int, attach_id: int) -> Response:
        """
        Download a file associated with a payment.

        :param student_id: The ID of the student.
        :param attach_id: The ID of the attachment.
        :return: The response from the Classeviva API.
        :rtype: dict
        """
        return await self.module.request(
            "GET", f"/{student_id}/pagoonline/downloadfile/{attach_id}"
        )

    async def privacy(self, student_id: int) -> Response:
        """
        Get the privacy settings for a specific student.

        :param student_id: The ID of the student.
        :return: The response from the Classeviva API.
        :rtype: dict
        """
        return await self.module.request("GET", f"/{student_id}/pagoonline/getprivacy")

    async def download_file_privacy(self, student_id: int, file_id: int) -> Response:
        """
        Download a privacy file associated with a student.

        :param student_id: The ID of the student.
        :param file_id: The ID of the privacy file.
        :return: The response from the Classeviva API.
        :rtype: dict
        """
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
        """
        Set the privacy settings for a specific student.

        :param student_id: The ID of the student.
        :param name: The name of the parent.
        :param surname: The surname of the parent.
        :param fiscal_code: The fiscal code of the parent.
        :param relationship: The relationship of the parent to the student.
        :param iban: The IBAN of the parent.
        :param flag_privacy: The privacy flag.
        :param flag_coord: The coordination flag.
        :return: The response from the Classeviva API.
        :rtype: dict
        """
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
    """
    This module is used to make HTTP requests to Classeviva's parents module.
    """

    endpoint = "parents"

    @property
    def talks(self) -> ParentsTalks:
        """
        Get talks-related endpoints, which have been separated
        from here to avoid making too many functions in one class
        for the same endpoint.
        """
        return ParentsTalks(self)

    @property
    def overall_talks(self) -> ParentsOverallTalks:
        """
        Get overall talks-related endpoints, which have been separated
        from here to avoid making too many functions in one class
        for the same endpoint.
        """
        return ParentsOverallTalks(self)

    @property
    def payments(self) -> ParentsPayments:
        """
        Get payments-related endpoints, which have been separated
        from here to avoid making too many functions in one class
        for the same endpoint.
        """
        return ParentsPayments(self)
