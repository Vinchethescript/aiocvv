from typing import Optional, List
from datetime import datetime, timedelta
from ..utils import parse_date, parse_time, group_by_date
from ..modules import StudentsModule
from ..types import Date
from ..dataclasses import (
    SchoolDay,
    AbsenceDay,
    Event,
    AgendaDay,
    Subject,
    PartialSubject,
    Lesson,
    Period,
    Day,
)
from ..enums import (
    SchoolDayStatus,
    AbsenceCode,
    EventCode,
    LessonEvent,
    LessonStatus,
    NoteType,
    Weekday,
    SchoolDayStatus,
)


class Calendar:
    def __init__(self, module: StudentsModule, id: int):
        self.__module = module
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
        ret = (await self.__module.calendar(self.id, begin, end))["content"]
        return [self.__parse_school_day(day) for day in ret["calendar"]]

    async def get_absences(
        self, begin: Optional[Date] = None, end: Optional[Date] = None
    ):
        ret = await self.__module.absences(self.id, begin, end)
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
    ):
        ret = await self.__module.agenda(self.id, begin, end, event_code)

        if not separate_days:
            return [self.__parse_event(evt) for evt in ret["content"]["agenda"]]

        days = group_by_date(ret["content"]["agenda"], self.__parse_event)

        return [AgendaDay(date, events) for date, events in days.items()]

    async def get_lessons(
        self,
        begin: Date,
        end: Optional[Date] = None,
        *,
        subject: Optional[int] = None,
    ) -> List[Lesson]:
        ret = await self.__module.lessons(self.id, begin, end, subject=subject)
        return [self.__parse_lesson(l) for l in ret["content"]["lessons"]]

    async def get_periods(self):
        ret = await self.__module.periods(self.id)
        return [
            Period(
                code=period["periodCode"],
                position=period["periodPos"],
                description=period["periodDesc"],
                final=period["isFinal"],
                start=parse_date(period["dateStart"]),
                end=parse_date(period["dateEnd"]),
                miur_division_code=period["miurDivisionCode"],
            )
            for period in ret["content"]["periods"]
        ]

    async def get_day(self, start: Date, end: Optional[Date] = None):
        subjects = await self.__module.client.me.get_subjects()
        periods = await self.get_periods()
        schooldays = await self.__module.calendar(self.id, start, end or start)
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
        me = self.__module.client.me
        data = await self.__module.overview(self.id, start, end)
        data = data["content"]

        lessons = group_by_date(data["lessons"], self.__parse_lesson)
        agenda = group_by_date(data["agenda"], self.__parse_event, subjects)
        events = group_by_date(data["events"], self.__parse_absence)
        grades = group_by_date(data["grades"], me._parse_grade, subjects, periods)
        schooldays = group_by_date(schooldays["calendar"])
        notes = {}
        for type in NoteType:
            notes.update(group_by_date(data["notes"][type.value], me._parse_note, type))

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

    async def __call__(self, begin: Date, end: Date):
        if end < begin:
            raise ValueError("end date cannot be before begin date")
        # make it iterate between the days between the dates, including the two dates themselves
        subjects = await self.__module.client.me.get_subjects()
        periods = await self.get_periods()
        schooldays = await self.__module.calendar(self.id, begin, end or begin)
        schooldays = schooldays["content"]
        for day in range((end - begin).days + 1):
            date = begin + timedelta(days=day)
            yield list(
                filter(
                    lambda d: d.date == date,
                    await self.__do_get_day(subjects, periods, schooldays, begin, end),
                )
            )[0]
