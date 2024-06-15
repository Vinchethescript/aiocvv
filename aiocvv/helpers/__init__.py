"""
Helpers are useful classes that help you interact with the API more easily.

.. warning::
    Unless noted, helpers are not made to be manually constructed, but
    to be used through :attr:`~aiocvv.client.ClassevivaClient.me`.
"""

from .calendar.core import Calendar, Period
from .noticeboard import (  # pylint: disable=reimported
    MyNoticeboard,
    MyNoticeboard as Noticeboard,
    File,
    Attachment,
    NoticeboardItem,
)
