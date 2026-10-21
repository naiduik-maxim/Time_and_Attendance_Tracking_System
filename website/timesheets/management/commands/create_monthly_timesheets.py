from django.core.management.base import (
    BaseCommand,
    CommandError
)

from django.utils import timezone

from unit.models import Unit
from timesheets.models import Tabel
from timesheets.services import (
    sync_timesheet,
    TimesheetSyncError
)

class Command(BaseCommand):
    help = (
        "Автоматичне створення та синхронізація "
        "місячних табелів усіх підрозділів."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--month",
            type=int,
            help="Місяць табеля (1-12)",
        )

        parser.add_argument(
            "--year",
            type=int,
            help="Рік табеля",
        )

    def handle(self, *args, **options):
        today = timezone.localdate()

        month = options["month"] or today.month
        year = options["year"] or today.year

        if not 1 <= month <= 12:
            raise CommandError(
                "Місяць повинен бути від 1 до 12."
            )

        if not 1 <= year <= 9999:
            raise CommandError("Некоректний рік.")

        self.stdout.write(
            f"Обробка табелів за {month:02d}.{year}"
        )

        created_count = 0
        existing_count = 0
        errors_count = 0

        departments = Unit.objects.all()

        for department in departments:
            tabel, created = Tabel.objects.get_or_create(
                unit=department,
                t_month=month,
                t_year=year,
            )

            if created:
                created_count += 1

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Створено: {department.title}"
                    )
                )
            else:
                existing_count += 1

                self.stdout.write(
                    f"Вже існує: {department.title}"
                )

            try:
                result = sync_timesheet(tabel.pk)

                self.stdout.write(
                    f"  Працівників: {result['workers']}, "
                    f"документів: {result['documents']}"
                )

            except TimesheetSyncError as error:
                errors_count += 1

                self.stderr.write(
                    self.style.ERROR(
                        f"Помилка синхронізації "
                        f"{department.title}: {error}"
                    )
                )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Створено табелів: {created_count}"
            )
        )

        self.stdout.write(
            f"Вже існувало: {existing_count}"
        )

        self.stdout.write(
            f"Помилок синхронізації: {errors_count}"
        )

        if errors_count:
            raise CommandError(
                "Деякі табелі не вдалося синхронізувати."
            )
