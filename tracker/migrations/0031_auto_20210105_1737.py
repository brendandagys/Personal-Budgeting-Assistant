# Generated by Django 2.2.2 on 2021-01-05 17:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0030_remove_profile_secondary_currency'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recurring',
            name='type',
            field=models.CharField(choices=[('Credit', 'Credit (Bill)'), ('Debit', 'Debit')], max_length=20, verbose_name='Type'),
        ),
    ]