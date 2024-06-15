"""
This helper contains the Calendar class, which is used to
interact with the calendar endpoint of the Classeviva API.

This class is used to get information about the user's calendar,
such as school days, absences, events, grades, notes, and more.
"""

from typing import Optional, List, AsyncIterator
from datetime import datetime, timedelta, date
from ...utils import parse_date, group_by_date, create_repr
from ...modules import StudentsModule
from ...types import Date
from ...dataclasses import (
    SchoolDay,
    AbsenceDay,
    Event,
    AgendaDay,
    Subject,
    PartialSubject,
    Lesson,
    Day,
)
from ...enums import (
    SchoolDayStatus,
    AbsenceCode,
    EventCode,
    LessonEvent,
    LessonStatus,
    NoteType,
    Weekday,
)
from .period import Period


class Calendar:
    """
    Represents the whole calendar of a student.
    """

    def __init__(
        self, module: StudentsModule, id: int
    ):  # pylint: disable=redefined-builtin
        self.module = module
        self.id = id

    @staticmethod
    def __dateify(string: str):
        return datetime.strptime(string, "%Y-%m-%d").date()

    @staticmethod
    def __timeify(string: str):
        return datetime.strptime(string, "%Y-%m-%dT%H:%M:%S%z")

    @classmethod
    def __parse_lesson(cls, data: dict) -> List[Lesson]:
        return Lesson(
            id=data["evtId"],
            date=cls.__dateify(data["evtDate"]),
            type=LessonEvent(data["evtCode"]),
            position=data["evtHPos"],
            duration=data["evtDuration"],
            class_desc=data["classDesc"],
            subject=PartialSubject(data["subjectCode"], data["subjectDesc"]),
            status=LessonStatus(data["status"]) if "status" in data else None,
        )

    @classmethod
    def __parse_event(cls, ev: dict, subjects: List[Subject]):
        return Event(
            id=ev["evtId"],
            type=EventCode(ev["evtCode"]),
            start=cls.__timeify(ev["evtDatetimeBegin"]),
            end=cls.__timeify(ev["evtDatetimeEnd"]),
            full_day=ev["isFullDay"],
            notes=ev["notes"],
            author=ev["authorName"],
            class_desc=ev["classDesc"],
            subject=(
                list(filter(lambda s: s.id == ev["subjectId"], subjects))[0]
                if ev["subjectId"]
                else None
            ),
            homework=ev["homeworkId"],
            homework_item=ev.get("homeworkItem", None),
        )

    @classmethod
    def __parse_absence(cls, evt: dict):
        return AbsenceDay(
            id=evt["evtId"],
            type=AbsenceCode(evt["evtCode"]),
            date=cls.__dateify(evt["evtDate"]),
            justified=evt["isJustified"],
            position=evt["evtHPos"],
        )

    @staticmethod
    def __parse_school_day(data: dict):
        return SchoolDay(
            date=data["dayDate"],
            weekday=data["dayOfWeek"],
            status=SchoolDayStatus(data["dayStatus"]),
        )

    async def get_school_days(
        self, begin: Optional[Date] = None, end: Optional[Date] = None
    ) -> List[SchoolDay]:
        """
        Get the school days in a range of dates.

        :param begin: The start date.
        :param end: The end date.
        :return: A list of :class:`~aiocvv.dataclasses.SchoolDay` objects.
        """
        ret = (await self.module.calendar(self.id, begin, end))["content"]
        return [self.__parse_school_day(day) for day in ret["calendar"]]

    async def get_absences(
        self, begin: Optional[Date] = None, end: Optional[Date] = None
    ) -> List[AbsenceDay]:
        """
        Get the absences in a range of dates.

        :param begin: The start date.
        :param end: The end date.
        :return: A list of :class:`~aiocvv.dataclasses.AbsenceDay` objects.
        """
        ret = await self.module.absences(self.id, begin, end)
        return [
            AbsenceDay(
                id=evt["evtId"],
                type=AbsenceCode(evt["evtCode"]),
                date=parse_date(evt["evtDate"]),
                justified=evt["isJustified"],
                position=evt["evtHPos"],
            )
            for evt in ret["content"]["events"]
        ]

    async def get_agenda(
        self,
        begin: Date,
        end: Date,
        event_code: Optional[EventCode] = None,
        *,
        separate_days: bool = True,
    ) -> AgendaDay:
        """
        Get the agenda in a range of dates.

        :param begin: The start date.
        :param end: The end date.
        :param event_code: The event code to filter by.
        :param separate_days: Whether to separate the events by day.
        :return: A list of :class:`~aiocvv.dataclasses.AgendaDay` objects.
        """
        ret = await self.module.agenda(self.id, begin, end, event_code)
        subjects = await self.module.client.me.get_subjects()

        if not separate_days:
            return [
                self.__parse_event(evt, subjects) for evt in ret["content"]["agenda"]
            ]

        days = group_by_date(ret["content"]["agenda"], self.__parse_event, subjects)

        return [AgendaDay(date, events) for date, events in days.items()]

    async def get_lessons(
        self,
        begin: Date,
        end: Optional[Date] = None,
        *,
        subject: Optional[int] = None,
    ) -> List[Lesson]:
        """
        Get the lessons in a range of dates.

        :param begin: The start date.
        :param end: The end date.
        :param subject: The subject to filter by.
        :return: A list of :class:`~aiocvv.dataclasses.Lesson` objects.
        """

        ret = await self.module.lessons(self.id, begin, end, subject=subject)
        return [self.__parse_lesson(l) for l in ret["content"]["lessons"]]

    async def get_periods(self):
        """
        Get the periods of the student's school.

        :return: A list of :class:`~aiocvv.dataclasses.Period` objects.
        """

        ret = await self.module.periods(self.id)
        return [Period(self, **period) for period in ret["content"]["periods"]]

    async def get_day(self, start: Date, end: Optional[Date] = None):
        """
        Get all of the information available for a specific day,
        merging calendar, absences, agenda, grades, notes, and
        school days all together here.

        :param start: The date of the day.
        :param end: The end date.
        :return: A list of :class:`~aiocvv.dataclasses.Day` objects.
        """

        subjects = await self.module.client.me.get_subjects()
        periods = await self.get_periods()
        schooldays = await self.module.calendar(self.id, start, end or start)
        schooldays = schooldays["content"]
        return await self.__do_get_day(subjects, periods, schooldays, start, end)

    async def __do_get_day(
        self,
        subjects,
        periods,
        schooldays,
        start: Date,
        end: Optional[Date] = None,
    ) -> List[Day]:
        me = self.module.client.me
        data = await self.module.overview(self.id, start, end)
        data = data["content"]

        lessons = group_by_date(data["lessons"], self.__parse_lesson)
        agenda = group_by_date(data["agenda"], self.__parse_event, subjects)
        events = group_by_date(data["events"], self.__parse_absence)
        grades = group_by_date(
            data["grades"], me._parse_grade, subjects, periods
        )  # pylint: disable=protected-access
        schooldays = group_by_date(schooldays["calendar"])
        notes = {}
        for tp in NoteType:
            notes.update(
                group_by_date(data["notes"][tp.value], me._parse_note, tp)
            )  # pylint: disable=protected-access

        # merge all the days together without duplicates
        days = list(
            set(
                list(lessons.keys())
                + list(agenda.keys())
                + list(events.keys())
                + list(grades.keys())
                + list(notes.keys())
                + list(schooldays.keys())
            )
        )
        ret = []
        for d in days:
            try:
                schoolday = schooldays[d][0]
            except KeyError:
                # this day shouldn't even be returned, let's ignore it
                continue

            ret.append(
                Day(
                    date=d,
                    weekday=Weekday(schoolday["dayOfWeek"]),
                    status=SchoolDayStatus(schoolday["dayStatus"]),
                    lessons=lessons.get(d, []),
                    agenda=agenda.get(d, []),
                    events=events.get(d, []),
                    grades=grades.get(d, []),
                    notes=notes.get(d, []),
                )
            )

        return ret

    @staticmethod
    def __filter_check(begin: Date, day: int):
        def chk(d: Day):
            return d.date == begin + timedelta(days=day)

        return chk

    async def __call__(self, begin: Date, end: Date) -> AsyncIterator[Day]:
        """
        Iterate over the days in a range of dates, returning
        the information available for each day, merging calendar,
        absences, agenda, grades, notes, and school days all together here.
        """
        if end < begin:
            raise ValueError("end date cannot be before begin date")

        subjects = await self.module.client.me.get_subjects()
        periods = await self.get_periods()
        schooldays = await self.module.calendar(self.id, begin, end or begin)
        schooldays = schooldays["content"]
        for day in range((end - begin).days + 1):
            yield list(
                filter(
                    self.__filter_check(begin, day),
                    await self.__do_get_day(subjects, periods, schooldays, begin, end),
                )
            )[0]
