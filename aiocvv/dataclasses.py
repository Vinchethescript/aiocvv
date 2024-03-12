from dataclasses import dataclass
from .enums import *
from typing import Optional, List
from datetime import date, datetime
from .utils import create_repr


@dataclass(frozen=True)
class AbsenceDay:
    id: int
    type: AbsenceCode
    date: date
    justified: bool
    position: Optional[int]  # only if type is delay or exit

    def __int__(self):
        return self.id

    def __repr__(self) -> str:
        return create_repr(
            self, id=self.id, date=self.date, type=self.type, justified=self.justified
        )


@dataclass(frozen=True)
class SchoolDay:
    date: date
    weekday: Weekday
    status: SchoolDayStatus

    def __repr__(self):
        return create_repr(
            self, date=self.date, weekday=self.weekday, status=self.status
        )


@dataclass(frozen=True)
class PartialSubject:
    code: str
    description: Optional[str]


@dataclass(frozen=True)
class Event:
    id: int
    type: EventCode
    start: datetime
    end: datetime
    full_day: bool
    author: str
    class_desc: str
    notes: Optional[str] = None
    homework: Optional[int] = None
    homework_item: Optional[List[str]] = None
    subject: Optional[PartialSubject] = None

    def __int__(self):
        return self.id

    def __str__(self):
        return self.type.description

    def __repr__(self):
        return create_repr(
            self,
            id=self.id,
            type=self.type,
            start=self.start,
            end=self.end,
            author=self.author,
        )


@dataclass(frozen=True)
class AgendaDay:
    date: date
    events: List[Event]


@dataclass(frozen=True)
class Lesson:
    id: int
    date: date
    type: LessonEvent
    position: int
    duration: int
    class_desc: str
    subject: PartialSubject
    status: Optional[LessonStatus] = None

    def __int__(self):
        return self.id

    def __str__(self):
        return self.subject.description

    def __repr__(self):
        return create_repr(
            self,
            id=self.id,
            date=self.date,
            type=self.type,
            subject=self.subject,
            status=self.status,
        )


@dataclass(frozen=True)
class MIUR:
    code: str
    division: str


@dataclass(frozen=True)
class School:
    code: str
    name: str
    dedication: str
    city: str
    province: str
    miur: MIUR

    def __str__(self):
        return self.name

    def __repr__(self):
        return create_repr(
            self, code=self.code, name=self.name, city=self.city, province=self.province
        )


@dataclass(frozen=True)
class Period:
    code: str
    position: int
    description: str
    final: bool
    start: date
    end: date
    miur_division_code: Optional[str] = None

    def __str__(self):
        return self.description

    def __repr__(self):
        return create_repr(
            self,
            code=self.code,
            description=self.description,
            start=self.start,
            end=self.end,
            final=self.final,
        )


@dataclass(frozen=True)
class Note:
    id: int
    type: NoteType
    date: date
    text: str
    read: bool
    author_name: str

    def __int__(self):
        return self.id

    def __str__(self):
        return self.text

    def __repr__(self):
        return create_repr(
            self, id=self.id, date=self.date, type=self.type, read=self.read
        )


@dataclass(frozen=True)
class Teacher:
    id: str
    name: str

    def __int__(self):
        return self.id

    def __str__(self):
        return self.name

    def __repr__(self):
        return create_repr(self, id=self.id, name=self.name)


@dataclass(frozen=True)
class Subject:
    id: int
    description: str
    order: int
    teachers: List[Teacher]

    def __int__(self):
        return self.id

    def __str__(self):
        return self.description

    def __repr__(self):
        return create_repr(
            self,
            id=self.id,
            description=self.description,
            teachers=self.teachers if self.teachers > 1 else None,
        )


@dataclass(frozen=True)
class Grade:
    subject: Subject
    subject_code: str
    id: int
    code: GradeCode
    date: date
    value: int
    display_value: str
    position: int
    family_notes: str
    color: str
    canceled: bool
    underlined: bool
    period: Period
    component_position: int
    component_description: str
    weight: int
    grade_master_id: int
    skill_id: int
    skill_description: str
    skill_code: str
    skill_master_id: int

    def __str__(self):
        return self.display_value

    def __int__(self):
        return self.value

    def __repr__(self):
        return create_repr(
            self,
            id=self.id,
            subject=self.subject.description,
            value=self.value or self.display_value,
            date=self.date,
        )


@dataclass(frozen=True)
class Day(SchoolDay):
    date: date
    lessons: List[Lesson]
    agenda: List[Event]
    events: List[AbsenceDay]
    grades: List[Grade]
    notes: List[Note]

    def __repr__(self) -> str:
        return create_repr(
            self,
            date=self.date,
            weekday=self.weekday,
            lessons=self.lessons,
            agenda=self.agenda,
            events=self.events,
            grades=self.grades,
            notes=self.notes,
        )
