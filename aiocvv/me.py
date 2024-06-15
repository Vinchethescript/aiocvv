"""
This module contains the class that represents
students, teachers and parents all together.
"""

from datetime import datetime
from io import BytesIO
from typing import Optional
from .enums import UserType, GradeCode, NoteType
from .helpers import Noticeboard, Calendar
from .dataclasses import School, MIURData, Subject, Teacher as TeacherT, Grade, Note
from .utils import capitalize_name, group_by_date, parse_date


class Me:
    """
    Represents a Classeviva user, whether it's a student, a teacher or a parent.

    .. note::
        This class is not meant to be manually constructed, but to be
        used through the :class:`~aiocvv.client.ClassevivaClient` class.
    """

    def __init__(self, client, **kwargs):
        from .client import ClassevivaClient

        self.client: ClassevivaClient = client
        self.__card = kwargs
        self.__noticeboard = None

    @property
    def identity(self) -> str:
        """
        The user's identity.
        """
        return self.__card["ident"]

    @property
    def type(self) -> UserType:
        """
        The type of the logged in user.
        """
        return UserType(self.__card["usrType"])

    @property
    def id(self) -> int:
        """
        The user's ID.
        """
        return self.__card["usrId"]

    @property
    def school(self) -> School:
        """
        The user's school details.
        """
        return School(
            code=self.__card["schCode"],
            name=self.__card["schName"],
            dedication=self.__card["schDedication"],
            city=self.__card["schCity"],
            proince=self.__card["schProv"],
            miur_data=MIURData(
                self.__card["miurSchoolCode"], self.__card["miurDivisionCode"]
            ),
        )

    @property
    def first_name(self) -> str:
        """The user's first name."""
        return capitalize_name(self.__card["firstName"])

    @property
    def last_name(self) -> str:
        """The user's last name."""
        return capitalize_name(self.__card["lastName"])

    @property
    def name(self) -> str:
        """The user's full name."""
        return f"{self.first_name} {self.last_name}"

    @property
    def birth_date(self) -> datetime:
        """The user's birth date."""
        return datetime.strptime(self.__card["birthDate"], "%Y-%m-%d")

    @property
    def fiscal_code(self) -> str:
        """The user's fiscal code."""
        return self.__card["fiscalCode"]

    async def refresh(self):
        """Refresh the user's data."""
        self.__card = await getattr(self.client, self.type.name).get_card(self.id)

    async def get_enabled_apps(self):
        """Get the enabled apps for the user."""
        resp = await self.client.request("GET", "/misc/enabled-apps")
        return resp["content"].get("enabledApps", [])

    async def get_avatar(self) -> BytesIO:
        """
        Returns the user's avatar as a BytesIO object.
        """
        resp = await self.client.request("GET", f"/users/{self.identity}/avatar")
        ret = BytesIO(resp["content"])
        ret.name = f"{self.identity}.jpg"
        return ret

    @property
    def noticeboard(self) -> Noticeboard:
        """The user's noticeboard."""
        if self.__noticeboard is None:
            tp = self.type
            if tp == UserType.parent:
                tp = UserType.student

            self.__noticeboard = Noticeboard(
                self.id, getattr(self.client, tp.name + "s")
            )

        return self.__noticeboard


class Teacher(Me):
    """
    Represents a Classeviva teacher.

    .. note::
        This class is not meant to be manually constructed, but to be
        used through the :class:`~aiocvv.client.ClassevivaClient` class.

    .. warning::
        This class is not yet implemented. You have to use the
        :meth:`~aiocvv.client.ClassevivaClient.teachers.request`
        method to manually make requests to the Classeviva API.
    """

    pass


class Student(Me):
    """
    Represents a Classeviva student.

    .. note::
        This class is not meant to be manually constructed, but to be
        used through the :class:`~aiocvv.client.ClassevivaClient` class.
    """

    def __init__(self, client, **kwargs):
        super().__init__(client, **kwargs)
        self.__calendar = None

    @staticmethod
    def _parse_grade(data, subjects, periods):
        return Grade(
            subject=list(filter(lambda s: s.id == data["subjectId"], subjects))[0],
            subject_code=data["subjectCode"],
            id=data["evtId"],
            code=GradeCode(data["evtCode"]),
            date=datetime.strptime(data["evtDate"], "%Y-%m-%d").date(),
            value=data["decimalValue"],
            display_value=data["displayValue"],
            position=data["displaPos"],
            family_notes=data["notesForFamily"],
            color=data["color"],
            canceled=data["canceled"],
            underlined=data["underlined"],
            period=list(filter(lambda p: p.position == data["periodPos"], periods))[0],
            component_position=data["componentPos"],
            component_description=data["componentDesc"],
            weight=data["weightFactor"],
            skill_id=data["skillId"],
            grade_master_id=data["gradeMasterId"],
            skill_description=data["skillDesc"],
            skill_code=data["skillCode"],
            skill_master_id=data["skillMasterId"],
        )

    @staticmethod
    def _parse_note(data, type_: NoteType):
        return Note(
            id=data["evtId"],
            type=type_,
            text=data["evtText"],
            date=parse_date(data.get("evtBegin", None) or data["evtDate"]),
            author_name=capitalize_name(data["authorName"]),
            read=data["readStatus"],
            end=parse_date(data["evtEnd"]) if data.get("evtEnd") else None,
        )

    @property
    def calendar(self) -> Calendar:
        """The user's calendar."""
        if self.__calendar is None:
            self.__calendar = Calendar(self.client.students, self.id)

        return self.__calendar

    async def get_subjects(self, include_grades: bool = False) -> list[Subject]:
        """
        Get the user's subjects.

        :param include_grades: Whether to include the grades for each subject.
        :return: A list of the user's subjects.
        """
        resp = await self.client.students.subjects(self.id)
        resp = resp["content"]["subjects"]
        return [
            Subject(
                teachers=[
                    TeacherT(id=t["teacherId"], name=capitalize_name(t["teacherName"]))
                    for t in subject.pop("teachers", [])
                ],
                grades=await self.get_grades(subject) if include_grades else None,
                **subject,
            )
            for subject in resp
        ]

    async def get_grades(self, subject: Optional[Subject] = None) -> list[Grade]:
        """
        Get the user's grades.

        :param subject: The subject to get the grades from.
        """
        resp = await self.client.students.grades(
            self.id, subject.id if subject else None
        )
        periods = await self.calendar.get_periods()
        subjects = await self.get_subjects()
        return [
            self._parse_grade(g, subjects, periods) for g in resp["content"]["grades"]
        ]

    async def get_notes(self, type: Optional[NoteType] = None) -> list[Note]:
        """Get the user's notes."""

        resp = await self.client.students.notes(self.id, type.value if type else None)
        resp = resp["content"]
        notes = {}
        for t in NoteType:
            notes.update(group_by_date(resp[t.value], self._parse_note, t))

        ret = []
        for notess in notes.values():
            ret += list(notess)

        return ret


class Parent(Student):
    """
    Represents a Classeviva parent, which also has access to
    the students' data (refer to :class:`~aiocvv.me.Student`).

    .. note::
        This class is not meant to be manually constructed, but to be
        used through the :class:`~aiocvv.client.ClassevivaClient` class.
    """

    pass
