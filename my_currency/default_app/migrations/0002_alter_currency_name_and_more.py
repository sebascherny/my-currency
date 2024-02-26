# Generated by Django 4.0.1 on 2024-02-26 02:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('default_app', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='currency',
            name='name',
            field=models.CharField(max_length=20),
        ),
        migrations.AlterField(
            model_name='currencyexchangerate',
            name='rate_value',
            field=models.DecimalField(decimal_places=6, max_digits=18),
        ),
    ]
