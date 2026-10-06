from django.db import models
from unit.models import Unit
from workers.models import Worker
# Create your models here.

class Tabel(models.Model):
    t_month = models.SmallIntegerField(verbose_name="Місяць")
    t_year = models.SmallIntegerField(verbose_name="Рік")
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, db_column='id_unit', related_name='tabels', verbose_name="Підрозділ")

    class Meta:
        db_table = 'tabel'
        verbose_name = "Табель"
        verbose_name_plural = "Табелі"

    def __str__(self):
        return f"Табель {self.t_month}/{self.t_year}"


class ContentTabel(models.Model):
    tabel = models.ForeignKey(Tabel, 
                              on_delete=models.CASCADE, 
                              db_column='id_tabel',
                              related_name='records')
    
    worker = models.ForeignKey(Worker, 
                               on_delete=models.CASCADE, 
                               db_column='id_worker', 
                               related_name='tabel_records')
    
    assignment = models.IntegerField(default=0, verbose_name="Відрядження (дні)")
    vacation = models.IntegerField(default=0, verbose_name="Відпустка (дні)")
    hospital = models.IntegerField(default=0, verbose_name="Лікарняний (дні)")
    skip_days = models.IntegerField(default=0, verbose_name="Пропуски (дні)")
    count_work_day = models.IntegerField(default=0, verbose_name="Робочі дні")

    class Meta:
        db_table = 'content_tabel'
        verbose_name = "Запис табеля"
        verbose_name_plural = "Записи табеля"