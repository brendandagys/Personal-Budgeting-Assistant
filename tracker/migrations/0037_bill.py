# Generated by Django 2.2.2 on 2020-12-12 17:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0036_delete_bill'),
    ]

    operations = [
        migrations.CreateModel(
            name='Bill',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bill', models.CharField(max_length=40, verbose_name='Bill')),
                ('active', models.BooleanField(default=True, verbose_name='Active')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=7, verbose_name='Amount')),
                ('frequency', models.CharField(max_length=100, verbose_name='Frequency')),
            ],
            options={
                'verbose_name': 'Bill',
                'verbose_name_plural': 'Bills',
            },
        ),
    ]
