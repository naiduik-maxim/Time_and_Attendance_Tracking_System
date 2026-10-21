from urllib.parse import urlencode

from django.views import View
from django.views.generic import ListView, CreateView
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.contrib import messages
from django.db import transaction
from django.db.models import Count, Sum
from django.db.models.functions import Coalesce
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from timesheets.models import Tabel
from workers.models import Worker
from .forms import UnitForm, WorkerHireForm, VacationLimitForm
from .models import Unit
# Create your views here.


class ManagerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.groups.filter(name='Managers').exists()


MONTH_NAMES = (
    'Січень', 'Лютий', 'Березень', 'Квітень', 'Травень', 'Червень',
    'Липень', 'Серпень', 'Вересень', 'Жовтень', 'Листопад', 'Грудень',
)


def chart_bar(label, value, maximum, kind):
    return {
        'label': label,
        'value': value,
        'width': max(2, round(value * 100 / maximum)) if value and maximum else 0,
        'kind': kind,
    }


class ManagerDashboardView(ManagerRequiredMixin, View):
    template_name = 'unit/manager_dashboard.html'

    def get_context(self, **extra):
        return {
            'departments': Unit.objects.annotate(
                worker_count=Count('workers', distinct=True),
            ).order_by('title', 'pk'),
            'unit_form': UnitForm(prefix='unit'),
            **extra,
        }

    def get(self, request):
        return render(request, self.template_name, self.get_context())

    def post(self, request):
        action = request.POST.get('action')
        if action == 'create_unit':
            form = UnitForm(request.POST, prefix='unit')
            if form.is_valid():
                unit = form.save()
                messages.success(request, 'Підрозділ створено.')
                return redirect('manager_department', pk=unit.pk)
            return render(request, self.template_name, self.get_context(
                unit_form=form, open_modal='unit-modal',
            ))

        return render(request, self.template_name, self.get_context(
            action_error='Невідома дія. Спробуйте ще раз.',
        ), status=400)


class ManagerDepartmentView(ManagerRequiredMixin, View):
    template_name = 'unit/manager_department.html'

    def redirect_to_period(self, unit, params, show_workers=False):
        url = reverse('manager_department', kwargs={'pk': unit.pk})
        query = {}
        if 'year' in params or 'month' in params:
            _, year, month = self.get_period(unit, params)
            query.update({'year': year, 'month': month or ''})
        if show_workers:
            query['workers'] = '1'
        if query:
            url += '?' + urlencode(query)
        return redirect(url)

    def get_period(self, unit, params):
        current_year = timezone.localdate().year
        years = sorted(set(Tabel.objects.filter(unit=unit).values_list('t_year', flat=True)) | {current_year}, reverse=True)
        year_text = str(params.get('year', current_year))
        year = int(year_text) if year_text.isdecimal() and int(year_text) in years else current_year
        month_text = str(params.get('month', ''))
        month = int(month_text) if month_text.isdecimal() and 1 <= int(month_text) <= 12 else None
        return years, year, month

    def get_context(self, unit, params, **extra):
        years, year, month = self.get_period(unit, params)
        monthly_stats = {
            row['t_month']: row
            for row in Tabel.objects.filter(unit=unit, t_year=year).values('t_month').annotate(
                timesheet_count=Count('pk', distinct=True),
                work_days=Coalesce(Sum('records__count_work_day'), 0),
                vacation_days=Coalesce(Sum('records__vacation'), 0),
                sick_days=Coalesce(Sum('records__hospital'), 0),
                assignment_days=Coalesce(Sum('records__assignment'), 0),
                skipped_days=Coalesce(Sum('records__skip_days'), 0),
            )
        }
        period_rows = [monthly_stats.get(month, {})] if month else list(monthly_stats.values())
        stats = {
            key: sum(row.get(key, 0) for row in period_rows)
            for key in ('timesheet_count', 'work_days', 'vacation_days', 'sick_days', 'assignment_days', 'skipped_days')
        }

        if month:
            categories = (
                ('Відпрацьовані дні', 'work_days', 'work'),
                ('Відпустка', 'vacation_days', 'vacation'),
                ('Лікарняний', 'sick_days', 'sick'),
                ('Відрядження', 'assignment_days', 'assignment'),
                ('Пропуски', 'skipped_days', 'skip'),
            )
            maximum = max((stats[key] for _, key, _ in categories), default=0)
            chart_rows = [
                {'label': label, 'bars': [chart_bar(label, stats[key], maximum, kind)]}
                for label, key, kind in categories
            ]
            chart_title = f'{MONTH_NAMES[month - 1]} {year}: розподіл днів'
        else:
            def other_days(row):
                return sum(row.get(key, 0) for key in ('sick_days', 'assignment_days', 'skipped_days'))

            maximum = max(
                (value for row in monthly_stats.values() for value in (
                    row.get('work_days', 0), row.get('vacation_days', 0), other_days(row),
                )),
                default=0,
            )
            chart_rows = [
                {
                    'label': label,
                    'bars': [
                        chart_bar('Відпрацьовані дні', monthly_stats.get(number, {}).get('work_days', 0), maximum, 'work'),
                        chart_bar('Відпустка', monthly_stats.get(number, {}).get('vacation_days', 0), maximum, 'vacation'),
                        chart_bar('Інші дні', other_days(monthly_stats.get(number, {})), maximum, 'other'),
                    ],
                }
                for number, label in enumerate(MONTH_NAMES, start=1)
            ]
            chart_title = f'{year}: динаміка за місяцями'

        workers = list(unit.workers.order_by('surname', 'firstname', 'pk'))
        return {
            'unit': unit,
            'workers': workers,
            'worker_count': len(workers),
            'years': years,
            'year': year,
            'month': month,
            'months': list(enumerate(MONTH_NAMES, start=1)),
            'stats': stats,
            'chart_rows': chart_rows,
            'chart_title': chart_title,
            'chart_has_data': any(stats[key] for key in ('work_days', 'vacation_days', 'sick_days', 'assignment_days', 'skipped_days')),
            'worker_form': WorkerHireForm(prefix='worker'),
            **extra,
        }

    def get(self, request, pk):
        unit = get_object_or_404(Unit, pk=pk)
        return render(request, self.template_name, self.get_context(
            unit, request.GET,
            open_modal='workers-modal' if request.GET.get('workers') == '1' else '',
        ))

    def post(self, request, pk):
        unit = get_object_or_404(Unit, pk=pk)
        action = request.POST.get('action')
        if action == 'create_worker':
            form = WorkerHireForm(request.POST, prefix='worker')
            if form.is_valid():
                worker = form.save(commit=False)
                worker.unit = unit
                worker.save()
                messages.success(request, 'Працівника додано.')
                return self.redirect_to_period(unit, request.POST)
            return render(request, self.template_name, self.get_context(
                unit, request.POST, worker_form=form, open_modal='worker-modal',
            ))

        if action == 'update_vacation':
            worker_id = request.POST.get('worker_id', '')
            if not worker_id.isdecimal():
                raise Http404('Працівника не знайдено.')
            worker = get_object_or_404(Worker, pk=worker_id, unit=unit)
            form = VacationLimitForm(request.POST, instance=worker)
            if form.is_valid():
                with transaction.atomic():
                    form.save()
                    if worker.user_id:
                        worker.user.vacation_limit = worker.vacation_limit
                        worker.user.save(update_fields=['vacation_limit'])
                messages.success(request, 'Ліміт відпустки оновлено.')
                return self.redirect_to_period(unit, request.POST, show_workers=True)
            return render(request, self.template_name, self.get_context(
                unit, request.POST, limit_form=form, limit_worker_id=worker.pk,
                open_modal='workers-modal',
            ))

        return render(request, self.template_name, self.get_context(
            unit, request.POST, action_error='Невідома дія. Спробуйте ще раз.',
        ), status=400)

class UnitListView(LoginRequiredMixin, ListView):
    model = Unit
    template_name = 'unit/unit_list.html'
    context_object_name = 'units'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_manage_units'] = (
            self.request.user.is_superuser
            or self.request.user.groups.filter(name='Managers').exists()
        )
        return context


class UnitCreateView(ManagerRequiredMixin, CreateView):
    model = Unit
    template_name = 'unit/unit_create.html'
    form_class = UnitForm
    def get_success_url(self):
        return reverse('manager_department', kwargs={'pk': self.object.pk})
