"""
This module is used to make HTTP requests to the students endpoint.
It can be used by students and parents, and not by teachers.
"""

import os
from datetime import datetime, date
from typing import Optional, Any, IO
from urllib.parse import urljoin
from io import BytesIO, StringIO
from base64 import b64encode
from .core import BaseModule
from ..enums import EventCode, NoteType
from ..types import Date, Response
from ..utils import convert_date


class StudentHomeworks:
    """
    Represents a collection of methods for managing student homeworks.
    """

    def __init__(self, module: "StudentsModule"):
        self.module = module

    async def all(self, student_id: int) -> Response:
        """
        Retrieves all of the student's homeworks.

        :param student_id: The ID of the student.
        :return: The response from the Classeviva API.
        :rtype: dict
        """

        return await self.module.request("GET", f"/{student_id}/homeworks")

    async def download_teacher_file(
        self, student_id: int, event_code: str, file_id: int
    ) -> Response:
        """
        Downloads a teacher file associated with a specific homework.

        :param student_id: The ID of the student.
        :param event_code: The event code of the homework.
        :param file_id: The ID of the file.
        :return: The response from the Classeviva API.
        :rtype: dict
        """

        return await self.module.request(
            "GET",
            f"/{student_id}/homeworks/downloadTeacherFile/{event_code}/{file_id}",
        )

    async def insert_student_msg(
        self, student_id: int, event_code: str, homework_id: int, message: str
    ) -> Response:
        """
        Inserts a message from the student for a specific homework.

        :param student_id: The ID of the student.
        :param event_code: The event code of the homework.
        :param homework_id: The ID of the homework.
        :param message: The message to insert.
        :return: The response from the Classeviva API.
        :rtype: dict
        """

        return await self.module.request(
            "POST",
            f"/{student_id}/homeworks/insertStudentMsg/{event_code}/{homework_id}",
            json={"studentMsg": message},
        )

    async def upload_student_file(
        self,
        student_id: int,
        event_code: str,
        homework_id: int,
        file: IO[Any],
        filename: Optional[str] = None,
    ) -> Response:
        """
        Uploads a file from the student for a specific homework.

        :param student_id: The ID of the student.
        :param event_code: The event code of the homework.
        :param homework_id: The ID of the homework.
        :param file: The file to upload.
        :param filename: The name of the file (optional).
        :return: The response from the Classeviva API.
        :rtype: dict
        """

        payload = {}
        if isinstance(file, (BytesIO, StringIO)):
            cont = file.getvalue()
        else:
            cont = file.read()

        if not filename and not file.name:
            raise ValueError("a file name must be specified")

        payload["file"] = await self.module.client.loop.run_in_executor(
            None, lambda: b64encode(cont).decode("utf-8")
        )
        payload["filename"] = os.path.basename(getattr(file, "name", None) or filename)
        return await self.module.request(
            "POST",
            f"/{student_id}/homeworks/uploadStudentFile/{event_code}/{homework_id}",
            json=payload,
        )

    async def set_teacher_msg_status(
        self,
        student_id: int,
        event_code: str,
        homework_id: int,
        read: bool = True,
    ) -> Response:
        """
        Sets the status of a teacher message for a specific homework.

        :param student_id: The ID of the student.
        :param event_code: The event code of the homework.
        :param homework_id: The ID of the homework.
        :param read: The status of the message (default: True).
        :return: The response from the Classeviva API.
        :rtype: dict
        """

        return await self.module.request(
            "POST",
            f"/{student_id}/homeworks/setTeacherMsgStatus/{event_code}/{homework_id}",
            json={"messageRead": read},
        )

    async def remove_student_file(
        self, student_id: int, event_code: str, homework_id: int, file_id: int
    ) -> Response:
        """
        Removes a file uploaded by the student for a specific homework.

        :param student_id: The ID of the student.
        :param event_code: The event code of the homework.
        :param homework_id: The ID of the homework.
        :param file_id: The ID of the file.
        :return: The response from the Classeviva API.
        :rtype: dict
        """

        return await self.module.request(
            "POST",
            f"/{student_id}/homeworks/removeStudentFile/{event_code}/{homework_id}/{file_id}",
        )


class StudentsModule(BaseModule):
    """
    This module is used to make HTTP requests to Classeviva's students module.
    """

    endpoint = "students"

    @property
    def homeworks(self) -> StudentHomeworks:
        """
        Get homeworks-related endpoints, which have been separated
        from here to avoid making too many functions in one class
        for the same endpoint.

        Note that this is for media that may be attached to homeworks.
        If you are looking for the homeworks from the agenda, use the
        :meth:`agenda` or the :meth:`overview` method instead.
        """
        return StudentHomeworks(self)

    async def calendar(
        self,
        student_id: int,
        start: Optional[Date] = None,
        end: Optional[Date] = None,
    ) -> Response:
        """
        Get information about the school's working, non-working and holiday days.

        .. note::
            Without the dates, it returns the whole calendar
            from the beginning to the end of the school year.

        :param student_id: The ID of the student.
        :param start: The start date of the calendar (optional).
        :param end: The end date of the calendar (optional).
        :return: The response from the Classeviva API.
        :rtype: dict
        :raises ValueError: If the end date is before the start date.
        """
        if start or end:
            start = getattr(start, "date", lambda: start)() or date.today()
            end = getattr(end, "date", lambda: end)() or date.today()

            if end < start:
                raise ValueError("end must be greater than start")

            start = convert_date(start)
            end = convert_date(end)
            ret = await self.request("GET", f"/{student_id}/calendar/{start}/{end}")
        else:
            ret = await self.request("GET", f"/{student_id}/calendar/all")

        return ret

    async def absences(
        self,
        student_id: int,
        start: Optional[Date] = None,
        end: Optional[Date] = None,
    ) -> Response:
        """
        Get the student's absences.

        :param student_id: The ID of the student.
        :param start: Optional. The start date of the absences, or the single absence day.
        :param end: Optional. The end date of the absences.

        :return: The response from the Classeviva API.
        :rtype: dict
        """
        if start or end:
            start = start or date.today()
            start = start.date() if isinstance(start, datetime) else start

            end = end.date() if isinstance(end, datetime) else end
            end = end if end and end >= start else ""

            start = convert_date(start)
            end = convert_date(end) if end else ""
            ret = await self.request(
                "GET", f"/{student_id}/absences/details/{start}/{end}"
            )
        else:
            ret = await self.request("GET", f"/{student_id}/absences/details")

        return ret

    async def agenda(
        self,
        student_id: int,
        start: Date,
        end: Date,
        event_code: Optional[EventCode] = None,
    ) -> Response:
        """
        Get the student's agenda (as in events, homeworks, etc.).

        :param student_id: The ID of the student.
        :param start: The start date of the agenda.
        :param end: The end date of the agenda.
        :param event_code: Optional. The event code to filter the agenda by.

        :return: The response from the Classeviva API.
        :rtype: dict
        :raises ValueError: If the end date is before the start date.
        """
        start = getattr(start, "date", lambda: start)()
        end = getattr(end, "date", lambda: end)()

        if end < start:
            raise ValueError("end must be greater than start")

        start = convert_date(start)
        end = convert_date(end)
        if event_code:
            ret = await self.request(
                "GET", f"/{student_id}/agenda/{event_code}/{start}/{end}"
            )
        else:
            ret = await self.request("GET", f"/{student_id}/agenda/all/{start}/{end}")

        return ret

    async def lessons(
        self,
        student_id,
        start: Date,
        end: Optional[Date] = None,
        *,
        subject: Optional[int] = None,
    ) -> Response:
        """
        Get the student's lessons.

        :param student_id: The ID of the student.
        :param start: The date from which to start retrieving lessons,
                            or the day to get lessons of.
        :param end: Optional. The date until which to retrieve lessons.
        :param subject: Optional. The ID of the subject to get the lessons of.

        :return: The response from the Classeviva API.
        :rtype: dict
        """

        today = not (start and end)

        start = convert_date(start, today=today)
        end = convert_date(end, today=today) if end else None

        base = f"/{student_id}/lessons"
        url = f"{base}-status/"
        params = [start, end] if not today else [start]
        if subject:
            if today:
                params.append(start)
            params.append(subject)

        join = "/".join(str(p) for p in params)
        url = urljoin(url, join)
        ret = await self.request("GET", url, raise_for_status=False)

        # Handle 404s by using the endpoint without status,
        # because the API limits the range of dates for status requests.
        # With this, we can still return lessons but without statuses.
        if ret["status"] == 404:
            ret = await self.request("GET", urljoin(base + "/", join))

        return ret

    async def periods(self, student_id: int) -> Response:
        """
        Get the student's school year periods.

        :param student_id: The ID of the student.

        :return: The response from the Classeviva API.
        :rtype: dict
        """
        return await self.request("GET", f"/{student_id}/periods")

    async def subjects(self, student_id: int) -> Response:
        """
        Get the student's subjects.

        :param student_id: The ID of the student.

        :return: The response from the Classeviva API.
        :rtype: dict
        """
        return await self.request("GET", f"/{student_id}/subjects")

    async def grades(self, student_id: int, subject: Optional[int] = None) -> Response:
        """
        Get the student's current grades.

        :param student_id: The ID of the student.
        :param subject: Optional. The ID of the subject to get the grades of.

        :return: The response from the Classeviva API.
        :rtype: dict
        """
        if subject:
            return await self.request(
                "GET", f"/{student_id}/grades2/subjects/{subject}"
            )

        return await self.request("GET", f"/{student_id}/grades2")

    async def notes(
        self,
        student_id: int,
        type: Optional[NoteType] = None,  # pylint: disable=redefined-builtin
        event: Optional[int] = None,
    ) -> Response:
        """
        Get the student's disciplinary notes.

        :param student_id: The ID of the student.
        :param type: Optional. The type of note to get.
        :param event: Optional. The ID of the note to get.

        :return: The response from the Classeviva API.
        :rtype: dict
        :raises ValueError: If the note ID is provided without the note type.
        """
        if event and not type:
            raise ValueError("event requires type")

        url = f"/{student_id}/notes/"
        meth = "GET"
        if type:
            url = urljoin(url, type.value) + "/"
            if event:
                url = urljoin(url, f"read/{event}")
                meth = "POST"
        else:
            url = urljoin(url, "all")

        return await self.request(meth, url)

    async def didactics(
        self, student_id: int, content_id: Optional[int] = None
    ) -> Response:
        """
        Get the didactics for a student.

        :param student_id: The ID of the student.
        :param content_id: Optional. The content ID.

        :return: The response from the Classeviva API.
        :rtype: dict
        """
        url = f"/{student_id}/didactics"
        if content_id:
            url = urljoin(url, f"item/{content_id}")

        return await self.request("GET", url)

    async def documents(
        self,
        student_id: int,
        hash: Optional[str] = None,  # pylint: disable=redefined-builtin
        *,
        check: Optional[bool] = False,
    ) -> Response:
        """
        Get the documents for a student.

        :param student_id: The ID of the student.
        :param hash: Optional. The hash of the document.
        :param check: Optional. Whether to check the document.

        :return: The response from the Classeviva API.
        :rtype: dict
        """
        url = f"/{student_id}/documents/"
        if hash:
            url = urljoin(url, f"{'check' if check else 'read'}/{hash}")

        return await self.request("POST", url)

    async def schoolbooks(self, student_id: int) -> Response:
        """
        Get the student's schoolbooks.

        :param student_id: The ID of the student.

        :return: The response from the Classeviva API.
        :rtype: dict
        """
        return await self.request("GET", f"/{student_id}/schoolbooks")

    async def register_config(self, student_id: int) -> Response:
        """
        Get the register configuration.

        :param student_id: The ID of the student.

        :return: The response from the Classeviva API.
        :rtype: dict
        """
        return await self.request("GET", f"/{student_id}/register-config")

    async def overview(
        self,
        student_id: int,
        start: Date,
        end: Optional[Date] = None,
    ) -> Response:
        """
        Get the student's agenda, lessons, events, grades and notes of a period, all in one request.

        :param student_id: The ID of the student.
        :param start: The start date of the overview or
                           the single day to get the overview of.
        :param end: Optional. The end date of the overview.

        :return: The response from the Classeviva API.
        :rtype: dict
        :raises ValueError: If the end date is before the start date.
        """
        if end and end < start:
            raise ValueError("end must be greater than start")

        start = convert_date(start)
        end = convert_date(end) if end else ""
        return await self.request("GET", f"/{student_id}/overview/all/{start}/{end}")

    async def virtual_classes(self, student_id: int):
        """
        Get the student's virtual classes.

        :param student_id: The ID of the student.
        :return: The response from the Classeviva API.
        :rtype: dict
        """
        return await self.request("GET", f"/{student_id}/virtualclasses/myclasses")
