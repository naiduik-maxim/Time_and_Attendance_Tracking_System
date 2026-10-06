from django.db import models
from workers.models import Worker
# Create your models here.

class TypeMissing(models.Model):
    name = models.CharField(max_length=50, verbose_name="Тип відсутності")

    class Meta:
        db_table = 'type_missing'
        verbose_name = "Тип відсутності"
        verbose_name_plural = "Типи відсутності"

    def __str__(self):
        return self.name


class Document(models.Model):
    worker = models.ForeignKey(Worker, to_field='tabel_num', on_delete=models.CASCADE, db_column='tabel_num', related_name='documents')
    type_missing = models.ForeignKey(TypeMissing, on_delete=models.CASCADE, db_column='id_type_missing', verbose_name="Причина")
    date_start = models.DateField(verbose_name="Дата початку")
    date_end = models.DateField(verbose_name="Дата кінця")
    description = models.TextField(blank=True, null=True, verbose_name="Опис")
    count_day = models.IntegerField(verbose_name="Кількість днів")

    class Meta:
        db_table = 'document'
        verbose_name = "Документ відсутності"
        verbose_name_plural = "Документи відсутності"