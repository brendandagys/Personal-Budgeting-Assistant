# Generated by Django 2.2.2 on 2020-02-12 20:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchase',
            name='category_2',
            field=models.CharField(blank=True, max_length=50, verbose_name='Category 2'),
        ),
    ]