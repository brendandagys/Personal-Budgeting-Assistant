# Generated by Django 2.2.2 on 2020-12-10 22:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0031_auto_20201210_2232'),
    ]

    operations = [
        migrations.AlterField(
            model_name='accountupdate',
            name='value',
            field=models.DecimalField(decimal_places=2, max_digits=9, verbose_name='Value'),
        ),
    ]