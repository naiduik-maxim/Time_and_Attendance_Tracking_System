from datetime import date
from io import BytesIO

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from openpyxl import load_workbook

from documents.models import Document, TypeMissing
from unit.models import Unit
from workers.models import Worker

from .export_view import get_timesheet_data
from .models import ContentTabel, Tabel
from .services import sync_timesheet


class TimesheetSyncTests(TestCase):
    def setUp(self):
        self.unit = Unit.objects.create(
            title='Тестовий відділ', code='TEST', manager='Керівник', address='Адреса',
        )
        self.worker = Worker.objects.create(
            id_passport='AA123', tabel_num='001', surname='Іваненко',
            firstname='Іван', lastname='Іванович', unit=self.unit,
            phone_num='123456789', post='Інженер', email='ivan@example.com',
            date_joined=date(2026, 10, 5),
        )
        self.tabel = Tabel.objects.create(unit=self.unit, t_month=10, t_year=2026)

    def add_document(self, kind, day):
        missing_type, _ = TypeMissing.objects.get_or_create(name=kind)
        return Document.objects.create(
            worker=self.worker, type_missing=missing_type,
            date_start=date(2026, 10, day), date_end=date(2026, 10, day),
            count_day=1,
        )

    def test_counts_elapsed_workdays_and_treats_assignment_as_work(self):
        self.add_document('vacation', 6)
        self.add_document('assignment', 7)
        self.add_document('skip', 8)

        first = sync_timesheet(self.tabel.pk, as_of=date(2026, 10, 9))
        record = ContentTabel.objects.get(tabel=self.tabel, worker=self.worker)
        self.assertEqual(first['created'], 1)
        self.assertEqual(record.count_work_day, 3)
        self.assertEqual((record.vacation, record.assignment, record.skip_days), (1, 1, 1))
        self.assertEqual(get_timesheet_data(self.tabel)[0][4], 3)

        second = sync_timesheet(self.tabel.pk, as_of=date(2026, 10, 9))
        self.assertEqual(second['created'], 0)
        self.assertEqual(second['updated'], 1)
        self.assertEqual(ContentTabel.objects.filter(tabel=self.tabel).count(), 1)

    def test_future_month_has_no_worked_days_yet(self):
        sync_timesheet(self.tabel.pk, as_of=date(2026, 9, 30))
        record = ContentTabel.objects.get(tabel=self.tabel, worker=self.worker)
        self.assertEqual(record.count_work_day, 0)

    def test_accountant_can_filter_by_year_and_export_workdays(self):
        accountant = get_user_model().objects.create_user(
            username='accountant', password='test-password',
        )
        self.unit.accountants.add(accountant)
        self.client.force_login(accountant)
        sync_timesheet(self.tabel.pk, as_of=date(2026, 10, 9))

        filtered = self.client.get(
            reverse('timesheets:department_timesheets', args=[self.unit.pk]),
            {'year': '2025'},
        )
        self.assertEqual(filtered.status_code, 200)
        self.assertEqual(list(filtered.context['timesheets']), [])

        detail = self.client.get(
            reverse('timesheets:accountant_timesheet_detail', args=[self.tabel.pk])
        )
        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, 'Відпрацьовані дні')

        excel = self.client.get(
            reverse('timesheets:timesheet_export_excel', args=[self.tabel.pk])
        )
        self.assertEqual(excel.status_code, 200)
        workbook = load_workbook(BytesIO(b''.join(excel.streaming_content)))
        self.assertEqual(workbook.active['E5'].value, 'Відпрацьовані дні')
        self.assertEqual(workbook.active['E6'].value, 5)

        pdf = self.client.get(
            reverse('timesheets:timesheet_export_pdf', args=[self.tabel.pk])
        )
        self.assertEqual(pdf.status_code, 200)
        self.assertTrue(b''.join(pdf.streaming_content).startswith(b'%PDF'))
