"""
This module contains all the enums used in the aiocvv package,
which are used for type hinting and for data that is always the same.
"""

# pylint: disable=invalid-name
from enum import Enum


class Weekday(Enum):
    """
    Represents the weekdays returned by the
    Classeviva API from the calendar endpoint.

    :ivar sunday: Sunday.
    :ivar monday: Monday.
    :ivar tuesday: Tuesday.
    :ivar wednesday: Wednesday.
    :ivar thursday: Thursday.
    :ivar friday: Friday.
    :ivar saturday: Saturday.
    """

    sunday = 1
    monday = 2
    tuesday = 3
    wednesday = 4
    thursday = 5
    friday = 6
    saturday = 7


class AbsenceCode(Enum):
    """
    Represents the absence codes.

    :ivar absence: You were absent.
    :ivar delay: You entered school late.
    :ivar short_delay: You entered school a little late.
    :ivar exit: You left school early.
    """

    absence = "ABA0"
    delay = "ABR0"
    short_delay = "ABR1"
    exit = "ABU0"


class SchoolDayStatus(Enum):
    """
    Represents the school day statuses.

    :ivar school: Normal school, working day.
    :ivar no_lesson: Day without lessons.
    :ivar holiday: Holiday.
    :ivar nonworking: Non-working day.
    :ivar undefined: Anything else?
    """

    school = "SD"
    no_lesson = "ND"
    holiday = "HD"
    nonworking = "NW"
    undefined = "US"


class EventCode(Enum):
    """
    Represents the event types for agenda.

    :ivar note: An annotation for that moment in the agenda.
    :ivar homework: An assignment for that day.
    :ivar reservation: A classroom reservation.
    """

    note = "AGNT"
    homework = "AGHW"
    reservation = "AGCR"


class LessonEvent(Enum):
    """
    Represents the lesson types.

    :ivar register: Normal lesson.
    :ivar co_presense: Co-presence lesson (there is more than one teacher).
    :ivar co_presense_support: Co-presence lesson with support.
    """

    register = "LSF0"
    co_presense = "LSC0"
    co_presense_support = "LSS0"


class LessonStatus(Enum):
    """
    Represents the student's presence status for a single lesson.

    :ivar present: The student was present.
    :ivar out: The student was out of class, but present in school.
    :ivar absent: The student was absent.
    :ivar no_lesson: There was no lesson at all.
    """

    present = "HAT0"
    out = "HAT1"
    absent = "HAB0"
    no_lesson = "HNN0"


class NoteType(Enum):
    """
    Represents the note types.

    :ivar teacher: An annotation made by a teacher.
    :ivar registry: A disciplinary note.
    :ivar warning: A warning note.
    :ivar sanction: A disciplinary sanction.
    """

    teacher = "NTTE"
    registry = "NTCL"
    warning = "NTWN"
    sanction = "NTST"


class RegisterType(Enum):
    """
    Represents the register types.

    :ivar standard: Standard register.
    :ivar simplified: Simplified register.
    """

    standard = "STD"
    simplified = "SMART"


class UserType(Enum):
    """
    Represents the user types.

    :ivar student: The user is a student.
    :ivar teacher: The user is a teacher.
    :ivar parent: The user is a parent.
    """

    student = "S"
    teacher = ""  # TODO: find out what this is
    parent = "G"


class GradeCode(Enum):
    """
    Represents the different grade types.

    :ivar decimal: A simple, normal grade.
    :ivar competences: A grade for competences.
    :ivar new_competences: A grade for new competences.
    :ivar entry_test: An entry test grade.
    :ivar pcto: A grade for the PCTO.
    """

    decimal = "GRV0"
    competences = "GRV1"
    new_competences = "GRV2"
    entry_test = "GRT1"
    pcto = "GRA1"
