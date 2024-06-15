import asyncio
import os
from datetime import timedelta, date
from aiocvv.client import ClassevivaClient as Client
from aiocvv.enums import SchoolDayStatus, AbsenceCode, EventCode, NoteType
from aiocvv.dataclasses import Grade, Note


async def main():
    # Log into the account
    client = await Client(os.getenv("CVV_USERNAME"), os.getenv("CVV_PASSWORD"))
    begin = date.today() - timedelta(days=7)
    end = date.today()
    final = [p for p in await client.me.calendar.get_periods() if p.final][-1]

    print(f"Hello, {client.me.name}. ", end="")

    if final.end < date.today():
        print("This school year is over! Let's see how you did this year.\n")
        total_grades = 0
        total_absences = 0
        total_notes = 0
        grades_sum = 0
        for period in await client.me.calendar.get_periods():
            grades = [g for g in await period.get_grades() if g.value is not None]
            notes = await period.get_notes()
            absences = await period.get_absences()

            total_grades += len(grades)
            total_absences += len(absences)
            total_notes += len(notes)

            grades_sum += sum(g.value for g in grades)

            avg = sum(g.value for g in grades) / len(grades)
            print(f"====== {period.description} ======")

            print(
                f"You got {len(grades)} grades, {len(notes)} notes and {len(absences)} absences."
            )
            print(f"Your average grade was {avg:.2f}.\n")
            print("Grades:")
            for grade in grades:
                print_grade(grade)

            print("\nAbsences:")
            for absence in absences:
                print(f"\t- {absence.date}: ", end="")
                if absence.type == AbsenceCode.absence:
                    print("Absence", end="")
                elif absence.type == AbsenceCode.delay:
                    print(f"Delay, you entered at position {absence.position}", end="")
                elif absence.type == AbsenceCode.short_delay:
                    print("Short delay", end="")
                elif absence.type == AbsenceCode.exit:
                    print(f"Exit, you left at position {absence.position}", end="")

                if not absence.justified:
                    print(" (not justified)", end="")

                print()

            print("\nNotes:")
            for note in notes:
                print_note(note)

            print()
            print()
            print()

        print(
            f"In total, you got {total_grades} grades, "
            f"{total_notes} notes and {total_absences} absences."
        )
        print(f"Your total average grade was {grades_sum / total_grades:.2f}.\n")
    else:

        print("Showing information for the last 7 days.\n")

        # Request information for each day using the iterator
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
                    print(
                        f"You left early! You left at position {event.position}.",
                        end="",
                    )

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
                    print_grade(grade)

            if day.notes:
                print("\nNotes:")
                for note in day.notes:
                    print_note(note)

        print()
        print()
        print()


def print_grade(grade: Grade):
    real_val = (
        f" ({grade.value})"
        if grade.value is not None and str(grade.value) != grade.display_value
        else ""
    )
    print(
        "\t- "
        + (grade.component_description + " " if grade.component_description else "")
        + f"{grade.subject}: {grade.display_value}{real_val}. {grade.family_notes}"
    )


def print_note(note: Note):
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


if __name__ == "__main__":
    if not os.getenv("CVV_USERNAME") or not os.getenv("CVV_PASSWORD"):
        raise ValueError(
            "Set CVV_USERNAME and CVV_PASSWORD environment variables first."
        )

    asyncio.run(main())
