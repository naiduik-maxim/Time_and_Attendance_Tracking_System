from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from unit.models import Unit
from workers.models import Worker

from .forms import DocumentForm
from .models import Document, TypeMissing


class DocumentFormTests(TestCase):
    def setUp(self):
        unit = Unit.objects.create(
            title='Тестовий відділ', code='TEST', manager='Керівник', address='Адреса',
        )
        self.worker = Worker.objects.create(
            id_passport='AA123', tabel_num='001', surname='Іваненко',
            firstname='Іван', lastname='Іванович', unit=unit,
            phone_num='123456789', post='Інженер', email='ivan@example.com',
            date_joined=date(2026, 10, 5),
        )
        self.missing_type = TypeMissing.objects.create(name='vacation')

    def form(self, **changes):
        data = {
            'type_missing': self.missing_type.pk,
            'date_start': '2026-10-05',
            'date_end': '2026-10-06',
            'count_day': 2,
            'description': 'Тест',
        }
        data.update(changes)
        return DocumentForm(data=data, worker=self.worker)

    def test_accepts_matching_weekday_count(self):
        self.assertTrue(self.form().is_valid())

    def test_rejects_inconsistent_or_reversed_dates(self):
        self.assertIn('count_day', self.form(count_day=9).errors)
        self.assertIn('date_end', self.form(date_end='2026-10-04').errors)
        self.assertIn('date_end', self.form(date_start='2026-10-10', date_end='2026-10-11').errors)

    def test_rejects_dates_before_hire_and_overlap(self):
        self.assertIn('date_start', self.form(date_start='2026-10-02').errors)
        Document.objects.create(
            worker=self.worker, type_missing=self.missing_type,
            date_start=date(2026, 10, 5), date_end=date(2026, 10, 5),
            count_day=1,
        )
        self.assertIn('date_start', self.form().errors)

    def test_create_endpoint_rejects_invalid_day_count(self):
        user = get_user_model().objects.create_user(
            username='worker', password='test-password',
        )
        user.groups.add(Group.objects.create(name='Workers'))
        self.worker.user = user
        self.worker.save(update_fields=['user'])
        self.client.force_login(user)

        response = self.client.post(
            reverse('document_create'),
            {
                'type_missing': self.missing_type.pk,
                'date_start': '2026-10-05',
                'date_end': '2026-10-06',
                'count_day': 9,
                'description': 'Тест',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Document.objects.count(), 0)

    def test_vacation_balance_counts_only_days_in_current_year(self):
        user = get_user_model().objects.create_user(
            username='worker', password='test-password',
        )
        user.groups.add(Group.objects.create(name='Workers'))
        self.worker.user = user
        self.worker.date_joined = date(2025, 1, 1)
        self.worker.save(update_fields=['user', 'date_joined'])
        Document.objects.create(
            worker=self.worker, type_missing=self.missing_type,
            date_start=date(2025, 12, 31), date_end=date(2026, 1, 2),
            count_day=3,
        )
        self.client.force_login(user)

        with patch('documents.views.timezone.localdate', return_value=date(2026, 1, 2)):
            response = self.client.get(reverse('document_list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['vacation_left'], 22)

    def test_vacation_balance_uses_worker_limit(self):
        user = get_user_model().objects.create_user(username='worker', password='test-password')
        user.groups.add(Group.objects.create(name='Workers'))
        self.worker.user = user
        self.worker.vacation_limit = 30
        self.worker.save(update_fields=['user', 'vacation_limit'])
        self.client.force_login(user)

        with patch('documents.views.timezone.localdate', return_value=date(2026, 10, 21)):
            response = self.client.get(reverse('document_list'))

        self.assertEqual(response.context['vacation_left'], 30)
