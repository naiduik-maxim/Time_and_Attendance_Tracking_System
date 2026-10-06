from django.db import models
from django.conf import settings
# Create your models here.

class Unit(models.Model):
    title = models.CharField(max_length=50, verbose_name="Назва")
    code = models.CharField(max_length=10, verbose_name="Код")
    manager = models.CharField(max_length=150, verbose_name="Керівник")
    address = models.TextField(verbose_name="Адреса")
    count_workers = models.IntegerField(default=0, verbose_name="Кількість працівників")

    accountants = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                         blank=True,
                                         verbose_name='Бухгалтери підрозіділу')

    class Meta:
        db_table = 'unit'
        verbose_name = "Підрозділ"
        verbose_name_plural = "Підрозділи"