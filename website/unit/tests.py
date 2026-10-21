from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from timesheets.models import ContentTabel, Tabel
from workers.models import Worker
from .models import Unit


class UnitCreateTests(TestCase):
    def test_superuser_can_create_unit(self):
        user = get_user_model().objects.create_superuser(
            username='admin', password='test-password', email='admin@example.com',
        )
        self.client.force_login(user)
        response = self.client.post(reverse('unit_create'), {
            'title': 'Відділ', 'code': 'DEP', 'manager': 'Керівник', 'address': 'Адреса',
        })
        unit = Unit.objects.get(code='DEP', address='Адреса')
        self.assertRedirects(response, reverse('manager_department', args=[unit.pk]))


class ManagerDepartmentTests(TestCase):
    def setUp(self):
        self.manager = get_user_model().objects.create_user(username='manager', password='test-password')
        self.manager.groups.add(Group.objects.create(name='Managers'))
        self.unit = Unit.objects.create(
            title='Виробництво', code='PROD', manager='Керівник', address='Адреса',
        )
        self.other_unit = Unit.objects.create(
            title='Продажі', code='SALES', manager='Менеджер', address='Київ',
        )
        self.worker = Worker.objects.create(
            id_passport='AA123', tabel_num='001', surname='Іваненко',
            firstname='Іван', lastname='Іванович', unit=self.unit,
            phone_num='123456789', post='Інженер', email='ivan@example.com',
            date_joined=date(2025, 1, 1),
        )
        self.client.force_login(self.manager)

    def detail_url(self, unit=None):
        return reverse('manager_department', args=[(unit or self.unit).pk])

    def test_dashboard_lists_departments_for_selection(self):
        response = self.client.get(reverse('manager_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.detail_url())
        self.assertContains(response, self.detail_url(self.other_unit))
        self.assertContains(response, 'id="unit-modal"')
        self.assertContains(response, 'id="department-search"')
        self.assertContains(response, 'data-department-card', count=2)
        self.assertNotContains(response, 'id="worker-modal"')

    def test_department_has_searchable_worker_window(self):
        response = self.client.get(self.detail_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="workers-modal"')
        self.assertContains(response, 'id="worker-search"')
        self.assertContains(response, 'data-worker-row')
        self.assertContains(response, 'data-open-modal="workers-modal"')

    def test_year_and_month_chart_use_selected_period(self):
        february = Tabel.objects.create(unit=self.unit, t_month=2, t_year=2026)
        march = Tabel.objects.create(unit=self.unit, t_month=3, t_year=2026)
        old = Tabel.objects.create(unit=self.unit, t_month=2, t_year=2025)
        ContentTabel.objects.create(
            tabel=february, worker=self.worker, count_work_day=18,
            vacation=3, hospital=2, assignment=1, skip_days=1,
        )
        ContentTabel.objects.create(tabel=march, worker=self.worker, count_work_day=17, vacation=2)
        ContentTabel.objects.create(tabel=old, worker=self.worker, count_work_day=20, vacation=4)

        with patch('unit.views.timezone.localdate', return_value=date(2026, 10, 21)):
            year_response = self.client.get(self.detail_url(), {'year': 2026})
            month_response = self.client.get(self.detail_url(), {'year': 2026, 'month': 2})

        self.assertEqual(year_response.status_code, 200)
        self.assertEqual(year_response.context['stats']['work_days'], 35)
        self.assertEqual(year_response.context['stats']['vacation_days'], 5)
        self.assertEqual(year_response.context['chart_rows'][1]['bars'][0]['value'], 18)
        self.assertEqual(year_response.context['chart_rows'][2]['bars'][0]['value'], 17)
        self.assertEqual(len(year_response.context['chart_rows']), 12)
        self.assertContains(year_response, '2026: динаміка за місяцями')

        self.assertEqual(month_response.context['month'], 2)
        self.assertEqual(month_response.context['stats']['work_days'], 18)
        self.assertEqual(month_response.context['stats']['vacation_days'], 3)
        self.assertEqual(month_response.context['stats']['sick_days'], 2)
        self.assertEqual(month_response.context['chart_rows'][0]['bars'][0]['value'], 18)
        self.assertContains(month_response, 'Лютий 2026: розподіл днів')

    def test_invalid_filter_falls_back_to_current_year(self):
        with patch('unit.views.timezone.localdate', return_value=date(2026, 10, 21)):
            response = self.client.get(self.detail_url(), {'year': '9999', 'month': '13'})
        self.assertEqual((response.context['year'], response.context['month']), (2026, None))

    def test_only_managers_can_open_or_change_departments(self):
        self.client.logout()
        self.assertEqual(self.client.get(self.detail_url()).status_code, 302)
        outsider = get_user_model().objects.create_user(username='outsider', password='test-password')
        self.client.force_login(outsider)
        self.assertEqual(self.client.get(self.detail_url()).status_code, 403)
        self.assertEqual(self.client.post(self.detail_url(), {
            'action': 'update_vacation', 'worker_id': self.worker.pk, 'vacation_limit': 10,
        }).status_code, 403)
        self.worker.refresh_from_db()
        self.assertEqual(self.worker.vacation_limit, 24)

    def test_unit_modal_redirects_to_new_department(self):
        response = self.client.post(reverse('manager_dashboard'), {
            'action': 'create_unit', 'unit-title': 'Склад', 'unit-code': 'STOCK',
            'unit-manager': 'Менеджер', 'unit-address': 'Київ',
        })
        unit = Unit.objects.get(code='STOCK')
        self.assertRedirects(response, self.detail_url(unit))

    def test_invalid_unit_form_reopens_modal(self):
        response = self.client.post(reverse('manager_dashboard'), {
            'action': 'create_unit', 'unit-title': 'Склад', 'unit-code': '',
            'unit-manager': 'Менеджер', 'unit-address': 'Київ',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['open_modal'], 'unit-modal')
        self.assertFalse(Unit.objects.filter(title='Склад').exists())

    def test_hire_is_bound_to_open_department_even_with_forged_unit(self):
        response = self.client.get(self.detail_url())
        self.assertNotIn('unit', response.context['worker_form'].fields)
        response = self.client.post(self.detail_url(), {
            'action': 'create_worker', 'worker-surname': 'Петренко',
            'worker-firstname': 'Петро', 'worker-lastname': 'Петрович',
            'worker-id_passport': 'BB456', 'worker-tabel_num': '002',
            'worker-phone_num': '123456789', 'worker-post': 'Аналітик',
            'worker-email': 'petro@example.com', 'worker-date_joined': '2026-10-21',
            'worker-unit': self.other_unit.pk,
        })
        self.assertRedirects(response, self.detail_url())
        self.assertEqual(Worker.objects.get(tabel_num='002').unit, self.unit)

    def test_invalid_hire_reopens_department_modal(self):
        response = self.client.post(self.detail_url(), {
            'action': 'create_worker', 'worker-surname': 'Петренко',
            'worker-firstname': 'Петро', 'worker-lastname': 'Петрович',
            'worker-id_passport': 'BB456', 'worker-tabel_num': '',
            'worker-phone_num': '123456789', 'worker-post': 'Аналітик',
            'worker-email': 'petro@example.com', 'worker-date_joined': '2026-10-21',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['open_modal'], 'worker-modal')
        self.assertFalse(Worker.objects.filter(surname='Петренко').exists())

    def test_vacation_limit_updates_only_worker_in_selected_department(self):
        user = get_user_model().objects.create_user(username='worker', password='test-password')
        self.worker.user = user
        self.worker.save(update_fields=['user'])
        response = self.client.post(self.detail_url(), {
            'action': 'update_vacation', 'worker_id': self.worker.pk, 'vacation_limit': 30,
        })
        self.assertRedirects(response, self.detail_url() + '?workers=1')
        self.worker.refresh_from_db()
        user.refresh_from_db()
        self.assertEqual((self.worker.vacation_limit, user.vacation_limit), (30, 30))

        response = self.client.post(self.detail_url(self.other_unit), {
            'action': 'update_vacation', 'worker_id': self.worker.pk, 'vacation_limit': 20,
        })
        self.assertEqual(response.status_code, 404)
        response = self.client.post(self.detail_url(), {
            'action': 'update_vacation', 'worker_id': self.worker.pk, 'vacation_limit': 366,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['limit_worker_id'], self.worker.pk)
        self.assertEqual(response.context['open_modal'], 'workers-modal')
        self.worker.refresh_from_db()
        self.assertEqual(self.worker.vacation_limit, 30)

    def test_dashboard_does_not_accept_general_hire(self):
        response = self.client.post(reverse('manager_dashboard'), {'action': 'create_worker'})
        self.assertEqual(response.status_code, 400)
