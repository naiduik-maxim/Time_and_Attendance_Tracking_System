from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.

class User(AbstractUser):
    vacation_limit = models.IntegerField(default=24, verbose_name='Ліміт відпустки (днів)')
    sick_limit = models.IntegerField(default=10, verbose_name='Ліміт лікарняних (днів)')

    class Meta:
        db_table = 'user'
        verbose_name = 'Користувач системи'
        verbose_name_plural = 'Користувачі системи'

