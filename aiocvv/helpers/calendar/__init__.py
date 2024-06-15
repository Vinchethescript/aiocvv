"""
This helper contains the Calendar and Period classes, which are used to
interact with the calendar endpoint of the Classeviva API.

The Calendar class is used to get information about the user's calendar,
such as school days, absences, events, grades, notes, and more.

The Period class is used to get information about the school
periods (e.g. first quarter, second quarter, etc.) and
everything that happened during them.
"""

from .core import Calendar
from .period import Period
