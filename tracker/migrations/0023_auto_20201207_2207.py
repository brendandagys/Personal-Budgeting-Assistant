# Generated by Django 2.2.2 on 2020-12-07 22:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0022_purchase_category_2'),
    ]

    operations = [
        migrations.AlterField(
            model_name='purchase',
            name='category_2',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='category_2', to='tracker.PurchaseCategory', verbose_name='Category 2'),
        ),
    ]
