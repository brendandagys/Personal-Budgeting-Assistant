# Generated by Django 2.2.2 on 2020-12-06 11:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0011_auto_20201206_1136'),
    ]

    operations = [
        migrations.AlterField(
            model_name='purchase',
            name='category_2',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='category_2', to='tracker.PurchaseCategory', verbose_name='Category 2'),
        ),
    ]
