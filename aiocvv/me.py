from datetime import datetime
from io import BytesIO
from typing import Optional
from .enums import UserType, GradeCode, NoteType
from .helpers import Noticeboard, Calendar
from .dataclasses import School, MIUR, Subject, Teacher as TeacherT, Grade, Note
from .utils import capitalize_name, group_by_date, parse_date


class Me:
    def __init__(self, client, **kwargs):
        from .client import ClassevivaClient

        self.client: ClassevivaClient = client
        self.__card = kwargs
        self.__noticeboard = None

    @property
    def identity(self):
        return self.__card["ident"]

    @property
    def type(self):
        return UserType(self.__card["usrType"])

    @property
    def id(self):
        return self.__card["usrId"]

    @property
    def school(self):
        return School(
            self.__card["schCode"],
            self.__card["schName"],
            self.__card["schDedication"],
            self.__card["schCity"],
            self.__card["schProv"],
            MIUR(self.__card["miurSchoolCode"], self.__card["miurDivisionCode"]),
        )

    @property
    def first_name(self):
        return capitalize_name(self.__card["firstName"])

    @property
    def last_name(self):
        return capitalize_name(self.__card["lastName"])

    @property
    def name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def birth_date(self):
        return datetime.strptime(self.__card["birthDate"], "%Y-%m-%d")

    @property
    def fiscal_code(self):
        return self.__card["fiscalCode"]

    async def refresh(self):
        self.__card = await getattr(self.client, self.type.name).get_card(self.id)

    async def get_enabled_apps(self):
        resp = await self.client.request("GET", "/misc/enabled-apps")
        return resp["content"].get("enabledApps", [])

    async def get_avatar(self) -> BytesIO:
        resp = await self.client.request("GET", f"/users/{self.identity}/avatar")
        ret = BytesIO(resp["content"])
        ret.name = f"{self.identity}.jpg"
        return ret

    @property
    def noticeboard(self):
        if self.__noticeboard is None:
            tp = self.type
            if tp == UserType.parent:
                tp = UserType.student

            self.__noticeboard = Noticeboard(
                self.id, getattr(self.client, tp.name + "s")
            )

        return self.__noticeboard


class Teacher(Me):
    pass


class Student(Me):
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
    def _parse_note(data, type: NoteType):
        return Note(
            id=data["evtId"],
            type=type,
            text=data["evtText"],
            date=parse_date(data["evtDate"]),
            author_name=capitalize_name(data["authorName"]),
            read=data["readStatus"],
        )

    @property
    def calendar(self):
        if self.__calendar is None:
            self.__calendar = Calendar(self.client.students, self.id)

        return self.__calendar

    async def get_subjects(self):
        resp = await self.client.students.subjects(self.id)
        resp = resp["content"]["subjects"]
        return [
            Subject(
                teachers=[
                    TeacherT(id=t["teacherId"], name=capitalize_name(t["teacherName"]))
                    for t in subject.pop("teachers", [])
                ],
                **subject,
            )
            for subject in resp
        ]

    async def get_grades(self, subject: Optional[Subject] = None):
        resp = await self.client.students.grades(
            self.id, subject.id if subject else None
        )
        periods = await self.calendar.get_periods()
        subjects = await self.get_subjects()
        return [
            self._parse_grade(g, periods, subjects) for g in resp["content"]["grades"]
        ]

    async def get_notes(self):
        resp = await self.client.students.notes(self.id)
        resp = resp["content"]
        notes = {}
        for type in NoteType:
            notes.update(group_by_date(resp[type.value], self._parse_note, type))

        ret = []
        for notess in notes.values():
            ret += list(notess)

        return ret


class Parent(Student):
    pass
