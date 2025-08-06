from django.db import models
from django.utils import timezone

class DailyRecord(models.Model):
    """日々の記録を保存するモデル"""

    WEATHER_CHOICES = [
        ('sunny', '晴れ'),
        ('cloudy', 'くもり'),
        ('rainy', '雨'),
    ]

    RATING_CHOICES = [
        ('S', 'S'),
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
    ]

    MEDICINE_CHOICES = [
        ('yes', '〇'),
        ('no', '×'),
        ('unknown', '不明'),
    ]

    date = models.DateField(
        verbose_name='日付',
        default=timezone.now,
        unique=True,
        help_text='記録する日付'
    )
    weather = models.CharField(
        verbose_name='天気',
        max_length=10,
        choices=WEATHER_CHOICES,
        blank=True
    )
    max_pressure = models.IntegerField(
        verbose_name='最高気圧 (hPa)',
        null=True,
        blank=True,
        help_text='ヘクトパスカルで入力'
    )
    min_pressure = models.IntegerField(
        verbose_name='最低気圧 (hPa)',
        null=True,
        blank=True,
        help_text='ヘクトパスカルで入力'
    )
    max_temperature = models.FloatField(
        verbose_name='最高気温 (°C)',
        null=True,
        blank=True,
        help_text='摂氏で入力'
    )
    min_temperature = models.FloatField(
        verbose_name='最低気温 (°C)',
        null=True,
        blank=True,
        help_text='摂氏で入力'
    )
    humidity = models.IntegerField(
        verbose_name='湿度 (%)',
        null=True,
        blank=True,
        help_text='パーセントで入力'
    )
    pollen = models.CharField(
        verbose_name='花粉状況',
        max_length=1,
        choices=RATING_CHOICES,
        blank=True,
        help_text='Sが最も少なく、Dが最も多い'
    )
    pm25 = models.CharField(
        verbose_name='PM2.5飛散状況',
        max_length=1,
        choices=RATING_CHOICES,
        blank=True,
        help_text='Sが最も空気がきれいで、Dが最も汚れている'
    )
    my_mood = models.CharField(
        verbose_name='自分の機嫌',
        max_length=1,
        choices=RATING_CHOICES,
        help_text='Sが最も機嫌が良い'
    )
    wife_mood = models.CharField(
        verbose_name='妻の機嫌',
        max_length=1,
        choices=RATING_CHOICES,
        help_text='Sが最も機嫌が良い'
    )
    headache_medicine = models.CharField(
        verbose_name='頭痛薬接種',
        max_length=10,
        choices=MEDICINE_CHOICES,
        default='unknown'
    )
    mishap = models.BooleanField(
        verbose_name='失態の有無',
        default=False,
        help_text='自分や家族（妻以外）の失態'
    )
    diary = models.TextField(
        verbose_name='日記',
        blank=True
    )

    def __str__(self):
        return f"{self.date}"

    class Meta:
        verbose_name = '日々の記録'
        verbose_name_plural = '日々の記録'
        ordering = ['-date']
