# Generated by Django 4.0.1 on 2024-02-26 04:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('default_app', '0002_alter_currency_name_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='currency',
            options={'ordering': ('code',)},
        ),
    ]
