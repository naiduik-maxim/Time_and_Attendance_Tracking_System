from django.views.generic import ListView, DetailView, View
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    UserPassesTestMixin,
)
from django.db.models import Count, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.shortcuts import redirect

from unit.models import Unit
from workers.models import Worker
from .models import Tabel
from .services import sync_timesheet, TimesheetSyncError


MONTH = [
    (1, "Січень"),
    (2, "Лютий"),
    (3, "Березень"),
    (4, "Квітень"),
    (5, "Травень"),
    (6, "Червень"),
    (7, "Липень"),
    (8, "Серпень"),
    (9, "Вересень"),
    (10, "Жовтень"),
    (11, "Листопад"),
    (12, "Грудень"),
]


class AccountantRequiredMixin(LoginRequiredMixin,UserPassesTestMixin):
    raise_exception = True

    def test_func(self):
        return Unit.objects.filter(
            accountants=self.request.user
        ).exists()


class AccountantDashboardView(AccountantRequiredMixin,ListView):
    model = Unit
    template_name = 'timesheets/accountant/dashboard.html'
    context_object_name = 'departments'

    def get_queryset(self):
        return (
            Unit.objects.filter(accountants=self.request.user)
            .annotate(tabel_count=Count('tabels', distinct=True))
            .order_by('title')
        )


class DepartmentTimesheetsView(AccountantRequiredMixin, ListView):
    model = Tabel
    template_name = 'timesheets/accountant/department.html'
    context_object_name = 'timesheets'

    def get_queryset(self):
        self.department = get_object_or_404(
            Unit.objects.filter(
                accountants=self.request.user
            ),
            pk=self.kwargs['department_id'],
        )

        queryset = Tabel.objects.filter(
            unit=self.department
        )

        self.selected_month = None
        self.selected_year = None

        month = self.request.GET.get('month', '')
        year = self.request.GET.get('yeat', '')

        if month.isdigit() and 1 <= int(month) <= 12:
            self.selected_month = int(month)
            queryset = queryset.filter(
                t_month=self.selected_month
            )

        if year.isdigit() and 1900 <= int(year) <= 2100:
            self.selected_year = int(year)
            queryset = queryset.filter(
                t_year=self.selected_year
            )

        return queryset.order_by("-t_year", "-t_month", "-pk")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['department'] = self.department
        context['months'] = MONTH
        context["selected_month"] = self.selected_month
        context["selected_year"] = self.selected_year 
        context["years"] = (
            Tabel.objects
            .filter(unit=self.department)
            .order_by("-t_year")
            .values_list("t_year", flat=True)
            .distinct()
        )

        return context


class AccountantTimesheetDetailView(AccountantRequiredMixin, DetailView):
    model = Tabel
    template_name = "timesheets/accountant/timesheet_detail.html"
    context_object_name = 'timesheet'

    def get_queryset(self):
        return (
            Tabel.objects
            .filter(unit__accountants=self.request.user)
            .select_related("unit")
        )

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        try:
            sync_timesheet(self.object.pk)

        except TimesheetSyncError as error:
            messages.error(
                request,
                f"Не вдалося оновити табель: {error}"
            )

        context = self.get_context_data(
            object=self.object
        )

        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        timesheet = self.object

        workers = (
            Worker.objects.filter(unit=timesheet.unit)
            .annotate(
                total_skip_days=Coalesce(
                    Sum(
                        "tabel_records__skip_days",
                        filter=Q(
                            tabel_records__tabel=timesheet
                        ),
                    ),
                    Value(0),
                ),
                total_vacation=Coalesce(
                    Sum(
                        "tabel_records__vacation",
                        filter=Q(
                            tabel_records__tabel=timesheet
                        ),
                    ),
                    Value(0),
                ),
                total_hospital=Coalesce(
                    Sum(
                        "tabel_records__hospital",
                        filter=Q(
                            tabel_records__tabel=timesheet
                        ),
                    ),
                    Value(0),
                ),
                total_assignment=Coalesce(
                    Sum(
                        "tabel_records__assignment",
                        filter=Q(
                            tabel_records__tabel=timesheet
                        ),
                    ),
                    Value(0),
                ),
                record_count=Count(
                    "tabel_records",
                    filter=Q(
                        tabel_records__tabel=timesheet
                    ),
                ),
            ).order_by('surname', 'firstname','lastname')
        )
        workers = list(workers)
        context['workers'] = workers
        context['workers_count'] = len(workers)
        
        context['missing_record_count'] = sum(
            worker.record_count
            for worker in workers
        )

        context["total_skip_days"] = sum(
            worker.total_skip_days
            for worker in workers
        )
        context["months"] = dict(MONTH)

        return context


class AccountantTimesheetSyncView(AccountantRequiredMixin, View):
    http_method_names = ['post']

    def post(self, request, pk):
        tabel = get_object_or_404(
            Tabel,
            pk=pk,
            unit__accountants=request.user,
        )

        try:
            result = sync_timesheet(tabel.pk)

        except TimesheetSyncError as error:
            messages.error(
                request,
                f"Помилка синхронізації: {error}",
            )

        else:
            messages.success(
                request,
                (
                    "Табель успішно синхронізовано. "
                    f"Створено записів: {result['created']}. "
                    f"Оновлено: {result['updated']}. "
                    f"Оброблено документів: {result['documents']}."
                ),
            )

        return redirect(
            "timesheets:accountant_timesheet_detail",
            pk=tabel.pk,
        )
