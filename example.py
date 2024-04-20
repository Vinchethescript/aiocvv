import asyncio
import os
from datetime import timedelta, date
from aiocvv.client import ClassevivaClient as Client
from aiocvv.enums import SchoolDayStatus, AbsenceCode, EventCode, NoteType


async def main():
    client = await Client(os.getenv("CVV_USERNAME"), os.getenv("CVV_PASSWORD"))
    begin = date.today() - timedelta(days=7)
    end = date.today()
    print(f"Hello, {client.me.name}. Showing information for the last 7 days.\n")
    async for day in client.me.calendar(begin, end):
        if day.status != SchoolDayStatus.school:
            print(f"{day.date} isn't a school day.\n")
            continue

        print(f"====== What happened on {day.date}? ======")
        for event in day.events:
            if event.type == AbsenceCode.absence:
                print("You were absent!", end="")
            elif event.type == AbsenceCode.delay:
                print(
                    f"You arrived late! You entered at position {event.position}.",
                    end="",
                )
            elif event.type == AbsenceCode.short_delay:
                print("You had a small delay.", end="")
            elif event.type == AbsenceCode.exit:
                print(f"You left early! You left at position {event.position}.", end="")

            print(" This was justified." if event.justified else "")

        if day.lessons:
            print("\nLessons:")
            for lesson in day.lessons:
                print(
                    f"\t- {lesson.subject.description} at {lesson.position} hour"
                    f" for {lesson.duration} hour{'s' if lesson.duration != 1 else ''}"
                )

        if day.agenda:
            print("\nAgenda:")
            for event in day.agenda:
                msg = "\t- "
                if event.type == EventCode.homework:
                    msg += "Homework "
                elif event.type == EventCode.note:
                    msg += "Note "
                elif event.type == EventCode.reservation:
                    msg += "Classroom reservation "

                msg += f"by {event.author}"
                if not event.full_day:
                    msg += f" from {event.start} to {event.end}"

                msg += f": {event.notes}"
                print(msg)

        if day.grades:
            print("\nGrades:")
            for grade in day.grades:
                real_val = (
                    f" ({grade.value})"
                    if grade.value is not None
                    and str(grade.value) != grade.display_value
                    else ""
                )
                print(
                    "\t- "
                    + (
                        grade.component_description + " "
                        if grade.component_description
                        else ""
                    )
                    + f"{grade.subject}: {grade.display_value}{real_val}. {grade.family_notes}"
                )

        if day.notes:
            print("\nNotes:")
            for note in day.notes:
                msg = "\t- "
                if note.type == NoteType.registry:
                    msg += "Disciplinary note"
                elif note.type == NoteType.sanction:
                    msg += "Disciplinary sanction"
                elif note.type == NoteType.teacher:
                    msg += "Annotation"
                elif note.type == NoteType.warning:
                    msg += "Warning"

                msg += f" by {note.author_name} on {note.date}: {note.text}"
                print(msg)

        print()
        print()
        print()


if __name__ == "__main__":
    if not os.getenv("CVV_USERNAME") or not os.getenv("CVV_PASSWORD"):
        raise ValueError(
            "Set CVV_USERNAME and CVV_PASSWORD environment variables first."
        )

    asyncio.run(main())
