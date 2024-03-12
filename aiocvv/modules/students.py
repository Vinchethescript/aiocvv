import os
from .core import TSCommonModule
from datetime import datetime, date
from typing import Optional, Any, IO
from urllib.parse import urljoin
from ..enums import *
from ..dataclasses import *
from ..types import Response, Date
from ..utils import convert_date
from io import BytesIO, StringIO
from base64 import b64encode


class StudentHomeworks:
    def __init__(self, module: "StudentsModule"):
        self.module = module

    async def all(self, student_id: int) -> Response:
        return await self.module.request("GET", f"/{student_id}/homeworks")

    async def download_teacher_file(
        self, student_id: int, event_code: str, file_id: int
    ) -> Response:
        return await self.module.request(
            "GET",
            f"/{student_id}/homeworks/downloadTeacherFile/{event_code}/{file_id}",
        )

    async def insert_student_msg(
        self, student_id: int, event_code: str, homework_id: int, message: str
    ) -> Response:
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
        return await self.module.request(
            "POST",
            f"/{student_id}/homeworks/setTeacherMsgStatus/{event_code}/{homework_id}",
            json={"messageRead": read},
        )

    async def remove_student_file(
        self, student_id: int, event_code: str, homework_id: int, file_id: int
    ) -> Response:
        return await self.module.request(
            "POST",
            f"/{student_id}/homeworks/removeStudentFile/{event_code}/{homework_id}/{file_id}",
        )


class StudentsModule(TSCommonModule):
    endpoint = "students"

    @property
    def homeworks(self):
        return StudentHomeworks(self)

    async def calendar(
        self,
        student_id: int,
        start: Optional[Date] = None,
        end: Optional[Date] = None,
    ) -> Response:
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
        today = not (start and end)

        start = convert_date(start, today=today)
        end = convert_date(end, today=today) if end else None

        base = f"/{student_id}/lessons"
        url = f"{base}-status/"
        params = [start, end] if not today else [start]
        print(params)
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
        return await self.request("GET", f"/{student_id}/periods")

    async def subjects(self, student_id: int) -> Response:
        return await self.request("GET", f"/{student_id}/subjects")

    async def grades(self, student_id: int, subject: Optional[int] = None) -> Response:
        if subject:
            return await self.request(
                "GET", f"/{student_id}/grades2/subjects/{subject}"
            )

        return await self.request("GET", f"/{student_id}/grades2")

    async def notes(
        self,
        student_id: int,
        type: Optional[NoteType] = None,
        event: Optional[int] = None,
    ) -> Response:
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
        url = f"/{student_id}/didactics"
        if content_id:
            url = urljoin(url, f"item/{content_id}")

        return await self.request("GET", url)

    async def documents(
        self,
        student_id: int,
        hash: Optional[str] = None,
        *,
        check: Optional[bool] = False,
    ) -> Response:
        url = f"/{student_id}/documents/"
        if hash:
            url = urljoin(url, f"{'check' if check else 'read'}/{hash}")

        return await self.request("POST", url)

    async def schoolbooks(self, student_id: int) -> Response:
        return await self.request("GET", f"/{student_id}/schoolbooks")

    async def register_config(self, student_id: int) -> Response:
        return await self.request("GET", f"/{student_id}/register-config")

    async def overview(
        self,
        student_id: int,
        start: Date,
        end: Optional[Date] = None,
    ) -> Response:
        if end and end < start:
            raise ValueError("end must be greater than start")

        start = convert_date(start)
        end = convert_date(end) if end else ""
        return await self.request("GET", f"/{student_id}/overview/all/{start}/{end}")

    async def virtual_classes(self, student_id: int):
        return await self.request("GET", f"/{student_id}/virtualclasses/myclasses")
