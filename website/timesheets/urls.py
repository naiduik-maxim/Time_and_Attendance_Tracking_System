from django.urls import path

from .views import (
    AccountantDashboardView,
    DepartmentTimesheetsView,
    AccountantTimesheetDetailView,
    AccountantTimesheetSyncView,
)

from .export_view import (
    AccountantTimesheetPDFView,
    AccountantTimesheetExcelView,
)

app_name = "timesheets"

urlpatterns = [
    path(
        "accountant/",
        AccountantDashboardView.as_view(),
        name="accountant_dashboard",
    ),
    path(
        "accountant/departments/<int:department_id>/",
        DepartmentTimesheetsView.as_view(),
        name="department_timesheets",
    ),
    path(
        "accountant/timesheets/<int:pk>/",
        AccountantTimesheetDetailView.as_view(),
        name="accountant_timesheet_detail",
    ),
    path(
        "accountant/timesheets/<int:pk>/sync/",
        AccountantTimesheetSyncView.as_view(),
        name="accountant_timesheet_sync",
    ),

    path(
        "accountant/timesheets/<int:pk>/export/pdf/",
        AccountantTimesheetPDFView.as_view(),
        name="timesheet_export_pdf",
    ),

    path(
        "accountant/timesheets/<int:pk>/export/excel/",
        AccountantTimesheetExcelView.as_view(),
        name="timesheet_export_excel",
    ),
]