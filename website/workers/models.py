from django.db import models
from unit.models import Unit
# Create your models here.

class Worker(models.Model):
    id_passport = models.CharField(max_length=100, verbose_name="Номер паспорта")
    tabel_num = models.CharField(max_length=20, unique=True, verbose_name="Табельний номер")
    surname = models.CharField(max_length=50, verbose_name="Прізвище")
    firstname = models.CharField(max_length=50, verbose_name="Ім'я")
    lastname = models.CharField(max_length=50, verbose_name="По батькові")

    unit = models.ForeignKey(Unit,
                             on_delete=models.CASCADE,
                             db_column='id_unit_w',
                             related_name='workers',
                             verbose_name='Підрозділ'
                             )

    phone_num = models.CharField(max_length=13, verbose_name="Номер телефону")
    post = models.CharField(max_length=50, verbose_name="Посада")
    email = models.EmailField(max_length=255, verbose_name="Email")
    date_joined = models.DateField(verbose_name="Дата прийому на роботу") 

    class Meta:
        db_table = 'worker'
        verbose_name = "Працівник"
        verbose_name_plural = "Працівники"