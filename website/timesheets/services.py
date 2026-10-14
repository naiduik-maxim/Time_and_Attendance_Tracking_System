import calendar
from collections import defaultdict
from datetime import date, timedelta

from django.db import transaction
from django.db.models import Count

from documents.models import Document
from workers.models import Worker

from .models import Tabel, ContentTabel

COUNT_ONLY_WEEKDAYS = True


TYPE_TO_FIELD = {
    # Пропуски
    "skip": "skip_days",
    "skip_days": "skip_days",
    "пропуск": "skip_days",
    "пропуски": "skip_days",
    "прогул": "skip_days",
    "прогули": "skip_days",
    "відсутність без поважної причини": "skip_days",

    # Відпустка
    "vacation": "vacation",
    "відпустка": "vacation",
    "щорічна відпустка": "vacation",

    # Лікарняний
    "hospital": "hospital",
    "лікарняний": "hospital",
    "тимчасова непрацездатність": "hospital",

    # Відрядження
    "assignment": "assignment",
    "відрядження": "assignment",
}


class TimesheetSyncError(Exception):
    """Помилка синхронізації табеля."""
    pass


def get_month_range(year, month):
    """
    Повертає початкову та кінцеву дату місяця.
    """

    if not 1 <= month <= 12:
        raise TimesheetSyncError(
            "Некоректний місяць табеля."
        )

    start = date(year, month, 1)

    last_day = calendar.monthrange(
        year, month
    )[1]

    end = date(year, month, last_day)

    return start, end


def normalize_type(name):
    """
    Нормалізує назву типу відсутності.
    """

    return " ".join(name.casefold().split())


def iter_counted_days(start, end):
    """
    Генерує дні в заданому періоді включно.

    Якщо COUNT_ONLY_WEEKDAYS=True,
    суботи та неділі не враховуються.
    """

    current = start

    while current <= end:

        if (
            not COUNT_ONLY_WEEKDAYS
            or current.weekday() < 5
        ):
            yield current

        current += timedelta(days=1)


@transaction.atomic
def sync_timesheet(tabel_id):
    """
    Синхронізує Document -> ContentTabel.

    - Враховує місяць і рік табеля.
    - Розподіляє дні за типами відсутності.
    - Створює відсутні записи працівників.
    - Оновлює наявні записи.
    - Не рахує однакову дату двічі.
    """

    tabel = (
        Tabel.objects
        .select_for_update()
        .select_related("unit")
        .get(pk=tabel_id)
    )

    month_start, month_end = get_month_range(
        tabel.t_year,
        tabel.t_month
    )

    workers = list(
        Worker.objects
        .filter(unit=tabel.unit)
        .order_by("pk")
    )

    workers_by_number = {
        worker.tabel_num: worker
        for worker in workers
    }

    documents = list(
        Document.objects
        .filter(
            worker__unit=tabel.unit,

            date_start__lte=month_end,

            date_end__gte=month_start,
        )
        .select_related(
            "type_missing",
            "worker"
        )
        .order_by("pk")
    )

    fields = (
        "skip_days",
        "vacation",
        "hospital",
        "assignment",
    )

    days_by_worker = defaultdict(
        lambda: {
            field: set()
            for field in fields
        }
    )

    for document in documents:

        type_name = normalize_type(
            document.type_missing.name
        )

        target_field = TYPE_TO_FIELD.get(
            type_name
        )

        if target_field is None:
            raise TimesheetSyncError(
                f"Невідомий тип відсутності "
                f"'{document.type_missing.name}' "
                f"у документі №{document.pk}."
            )

        if document.date_end < document.date_start:
            raise TimesheetSyncError(
                f"Некоректний період "
                f"у документі №{document.pk}."
            )

        worker_number = document.worker_id

        if worker_number not in workers_by_number:
            raise TimesheetSyncError(
                f"Працівника документа №{document.pk} "
                "не знайдено в підрозділі."
            )

        start = max(
            document.date_start,
            month_start
        )

        end = min(
            document.date_end,
            month_end
        )

        worker_days = days_by_worker[
            worker_number
        ]

        for day in iter_counted_days(start, end):

            for other_field in fields:

                if (
                    other_field != target_field
                    and day in worker_days[other_field]
                ):
                    raise TimesheetSyncError(
                        f"Конфлікт документів "
                        f"працівника {worker_number}: "
                        f"дата {day} належить "
                        "до різних типів відсутності."
                    )

            worker_days[target_field].add(day)


    duplicates = (
        ContentTabel.objects
        .filter(tabel=tabel)
        .values("worker_id")
        .annotate(total=Count("pk"))
        .filter(total__gt=1)
    )

    if duplicates.exists():
        raise TimesheetSyncError(
            "У табелі є дубльовані записи "
            "для одного працівника."
        )

    created_count = 0
    updated_count = 0

    totals = {
        field: 0
        for field in fields
    }

    for worker in workers:

        worker_days = days_by_worker[
            worker.tabel_num
        ]

        defaults = {
            field: len(worker_days[field])
            for field in fields
        }

        for field in fields:
            totals[field] += defaults[field]

        record, created = (
            ContentTabel.objects.update_or_create(
                tabel=tabel,
                worker=worker,
                defaults=defaults,
            )
        )

        if created:
            created_count += 1
        else:
            updated_count += 1

    return {
        "created": created_count,
        "updated": updated_count,
        "workers": len(workers),
        "documents": len(documents),
        "totals": totals,
    }