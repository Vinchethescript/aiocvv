"""
This is where the dataclasses used to represent the Classeviva API responses are defined.

They are used to represent the data returned by the API in a more structured and easy-to-use way.

.. warning:: 
    These should **NOT** be manually constructed, as they are returned
    by the methods from :attr:`~aiocvv.client.ClassevivaClient.me`.

    In this case, parameters should be considered as attributes, and not as parameters.
    Dataclasses are frozen, which means that they're immutable and cannot be changed after creation.
"""

from dataclasses import dataclass
from typing import Optional, List
from datetime import date, datetime
from .enums import (
    AbsenceCode,
    Weekday,
    SchoolDayStatus,
    EventCode,
    LessonEvent,
    LessonStatus,
    NoteType,
    GradeCode,
)
from .utils import create_repr


@dataclass(frozen=True)
class AbsenceDay:
    """
    Represents an absence day.
    This could be either a full-day absence, a (small) delay or an early exit.

    :param id: The ID of the absence.
    :param type: The type of absence.
    :param date: The day of the absence.
    :param justified: Whether the absence is justified.
    :param position: The position of the delay or exit.
    """

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
    """
    Represents a school day.

    :param date: The date.
    :param weekday: The day weekday.
    :param status: The kind of day (normal, non-working, etc.).
    """

    date: date
    weekday: Weekday
    status: SchoolDayStatus

    def __repr__(self):
        return create_repr(
            self, date=self.date, weekday=self.weekday, status=self.status
        )


@dataclass(frozen=True)
class PartialSubject:
    """
    Represents a partial subject.

    :param code: The subject code.
    :param description: The subject description.
    """

    code: str
    description: Optional[str]


@dataclass(frozen=True)
class Event:
    """
    Represents an agenda event.

    :param id: The ID of the event.
    :param type: The kind of event (annotation, homework, or classroom reservation).
    :param start: The start date and time.
    :param end: The end date and time.
    :param full_day: Whether the event is full-day or not.
    :param author: The author (a teacher in most cases) of the event.
    :param class_desc: The description of the classroom.
    :param notes: The actual text of the event.
    :param homework: The homework ID, if homework is provided.
    :param homework_item: The homework item, if homework is provided.
    :param subject: The subject of the event.
    """

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
        return self.class_desc

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
    """
    Represents a day for the agenda.

    :param date: The date.
    :param events: The events of the day.
    """

    date: date
    events: List[Event]


@dataclass(frozen=True)
class Lesson:
    """
    Represents a lesson.

    :param id: The ID of the lesson.
    :param date: The date of the lesson.
    :param type: The type of lesson (normal or co-presence with and without support).
    :param position: The position of the lesson in that day.
    :param duration: The duration of the lesson.
    :param class_desc: The description of the classroom.
    :param subject: The subject of the lesson.
    :param status: The status of the lesson.
    """

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
class MIURData:
    """
    Represents data provided from the MIUR.

    :param code: The school code.
    :param division: The school division code.
    """

    code: str
    division: str


@dataclass(frozen=True)
class School:
    """
    Represents a school.

    :param code: The school code.
    :param name: The school name.
    :param dedication: The dedication of the school.
    :param city: The city of the school.
    :param province: The province of the school.
    :param miur: The school's data from MIUR.
    """

    code: str
    name: str
    dedication: str
    city: str
    province: str
    miur_data: MIURData

    def __str__(self):
        return self.name

    def __repr__(self):
        return create_repr(
            self, code=self.code, name=self.name, city=self.city, province=self.province
        )


@dataclass(frozen=True)
class Note:
    """
    Represents a school note.

    :param id: The ID of the note.
    :param type: The type of the note (annotation, disciplinary, warning and sanction).
    :param date: The day the note has been created.
    :param text: The text of the note.
    :param read: Whether the note has been read.
    :param author_name: The name of the author of the note.
    :param end: Optional. The day the disciplinary sanction ends. Only available when :attr:`type` is `sanction`.
    """

    id: int
    type: NoteType
    end: Optional[date]
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
    """
    Represents a teacher.

    :param id: The ID of the teacher.
    :param name: The name of the teacher.
    """

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
    """
    Represents a subject.

    :param id: The ID of the subject.
    :param description: The description of the subject.
    :param order: The position of the subject for a UI.
    :param teachers: The teachers that teach the subject.
    """

    id: int
    description: str
    order: int
    teachers: List[Teacher]
    grades: Optional[List["Grade"]]

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
    """
    Represents a subject grade.

    :param subject: The subject of the grade.
    :param subject_code: The subject's shorter name.
    :param id: The ID of the grade.
    :param code: The kind of grade.
    :param date: The day the grade has been given.
    :param value: The actual value of the grade. (e.g. 6.25)
    :param display_value: The display value of the grade. (e.g. 6.25 is displayed as 6+)
    :param position: The position of the grade.
    :param family_notes: The notes of the grade visible to family and students.
    :param color: The color of the grade.
    :param canceled: Whether the grade has been canceled.
    :param underlined: Whether the grade is underlined.
    :param period: The period of the grade.
    :param component_position: The position of the component.
    :param component_description: The description of the component.
    :param weight: The weight of the grade.
    :param grade_master_id: The ID of the grade master.
    :param skill_id: The ID of the skill.
    :param skill_description: The description of the skill.
    :param skill_code: The code of the skill.
    :param skill_master_id: The ID of the skill master.
    """

    subject: Subject
    subject_code: str
    id: int
    code: GradeCode
    date: date
    value: Optional[int]
    display_value: str
    position: int
    family_notes: str
    color: str
    canceled: bool
    underlined: bool
    period: "Period"
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
    """
    Represents a full overview of a day.

    :param date: The date.
    :param weekday: The day weekday.
    :param status: The kind of day (normal, non-working, etc.).
    :param lessons: The lessons of that day.
    :param agenda: The events of that day.
    :param events: The absences of that day.
    :param grades: The grades of that day.
    :param notes: The notes of that day.
    """

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


# This has been imported here to avoid circular imports
from .helpers.calendar.period import Period
