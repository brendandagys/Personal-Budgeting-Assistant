# Generated by Django 2.2.2 on 2020-12-29 20:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0012_auto_20201221_2029'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recurring',
            name='type',
            field=models.CharField(choices=[('Credit', 'Credit'), ('Debit', 'Debit')], max_length=20, verbose_name='Type'),
        ),
    ]
