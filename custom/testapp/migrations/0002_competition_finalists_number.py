# Generated by Django 3.1.13 on 2023-09-10 22:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testapp', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='competition',
            name='finalists_number',
            field=models.IntegerField(default=0, verbose_name='Number of finalists per dance role'),
            preserve_default=False,
        ),
    ]