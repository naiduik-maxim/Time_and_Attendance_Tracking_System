from django.db import migrations, models
import django.core.validators


def copy_vacation_limits(apps, schema_editor):
    Worker = apps.get_model('workers', 'Worker')
    for worker in Worker.objects.exclude(user_id=None).select_related('user').iterator():
        limit = worker.user.vacation_limit
        worker.vacation_limit = max(0, min(365, limit))
        worker.save(update_fields=['vacation_limit'])


class Migration(migrations.Migration):
    dependencies = [
        ('workers', '0001_initial'),
        ('users', '0002_user_sick_limit_user_vacation_limit'),
    ]

    operations = [
        migrations.AddField(
            model_name='worker',
            name='vacation_limit',
            field=models.PositiveSmallIntegerField(
                default=24,
                validators=[django.core.validators.MaxValueValidator(365)],
                verbose_name='Ліміт відпустки (днів)',
            ),
        ),
        migrations.RunPython(copy_vacation_limits, migrations.RunPython.noop),
    ]
