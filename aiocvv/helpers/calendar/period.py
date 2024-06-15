"""
This helper contains the Period class, which is used to
get information about school periods and everything that
happened during them.
"""

from ...utils import parse_date, create_repr
from ...dataclasses import Grade, Subject, Note, AbsenceDay
from ...enums import NoteType
from ...types import date
from typing import List, Optional
from typing_extensions import Self


class Period:
    """
    Represents a school period (e.g. first quarter, second quarter, etc.).
    """

    def __init__(self, calendar, **data):

        self.__calendar = calendar
        self.__data = data

        self.__code: str = data["periodCode"]
        self.__position: int = data["periodPos"]
        self.__description: str = data["periodDesc"]
        self.__final: bool = data["isFinal"]
        self.__start: date = parse_date(data["dateStart"])
        self.__end: date = parse_date(data["dateEnd"])
        self.__miur: Optional[str] = data["miurDivisionCode"]

    @property
    def code(self) -> str:
        """The code of the period."""
        return self.__code

    @property
    def position(self) -> int:
        """The period's position."""
        return self.__position

    @property
    def description(self) -> str:
        """The description of the period."""
        return self.__description

    @property
    def final(self) -> bool:
        """Whether the period is final or not."""
        return self.__final

    @property
    def start(self) -> date:
        """The date of when the period starts."""
        return self.__start

    @property
    def end(self) -> date:
        """The date of when the period ends."""
        return self.__end

    @property
    def miur_division_code(self) -> Optional[str]:
        """The division code provided by MIUR, if any."""
        return self.__miur

    def __repr__(self):
        return create_repr(
            self,
            code=self.code,
            description=self.description,
            start=self.start,
            end=self.end,
            final=self.final,
        )

    def __str__(self):
        return self.description

    def __eq__(self, other: Self):
        return self.code == other.code

    async def get_grades(self, subject: Optional[Subject] = None) -> List[Grade]:
        """
        Get the grades that were given during the period.

        :return: A list of :class:`~aiocvv.dataclasses.Grade` objects.
        """
        resp = list(
            filter(
                lambda g: g["periodPos"] == self.position,
                (
                    await self.__calendar.module.grades(
                        self.__calendar.id, subject.id if subject else None
                    )
                )["content"]["grades"],
            )
        )

        me = self.__calendar.module.client.me
        subjects = await me.get_subjects()
        return [
            me._parse_grade(g, subjects, [self])  # pylint: disable=protected-access
            for g in resp
        ]

    async def get_notes(self, type: Optional[NoteType] = None) -> List[Note]:
        """
        Get the notes assigned during the period.

        :return: A list of :class:`~aiocvv.dataclasses.Note` objects.
        """
        ret: List[Note] = await self.__calendar.module.client.me.get_notes(type)
        return list(filter(lambda n: self.start <= n.date <= self.end, ret))

    async def get_absences(self) -> List[AbsenceDay]:
        """
        Get the days the student has been absent during this period.

        :return: A list of :class:`~aiocvv.dataclasses.AbsenceDay` objects.
        """
        return await self.__calendar.get_absences(self.start, self.end)
