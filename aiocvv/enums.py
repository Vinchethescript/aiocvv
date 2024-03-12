from enum import Enum


class Weekday(Enum):
    sunday = 1
    monday = 2
    tuesday = 3
    wednesday = 4
    thursday = 5
    friday = 6
    saturday = 7


class AbsenceCode(Enum):
    absence = "ABA0"
    delay = "ABR0"
    short_delay = "ABR1"
    exit = "ABU0"


class SchoolDayStatus(Enum):
    school = "SD"
    no_lesson = "ND"
    holiday = "HD"
    nonworking = "NW"
    undefined = "US"


class EventCode(Enum):
    note = "AGNT"
    homework = "AGHW"
    reservation = "AGCR"


class LessonEvent(Enum):
    register = "LSF0"
    co_presense = "LSC0"
    co_presense_support = "LSS0"


class LessonStatus(Enum):
    present = "HAT0"
    out = "HAT1"
    absent = "HAB0"
    no_lesson = "HNN0"


class NoteType(Enum):
    teacher = "NTTE"
    registry = "NTCL"
    warning = "NTWN"
    sanction = "NTST"


class RegisterType(Enum):
    standard = "STD"
    simplified = "SMART"


class UserType(Enum):
    student = "S"
    teacher = ""  # TODO: find out what this is
    parent = "G"


class GradeCode(Enum):
    decimal = "GRV0"
    competences = "GRV1"
    new_competences = "GRV2"
    entry_test = "GRT1"
    pcto = "GRA1"
