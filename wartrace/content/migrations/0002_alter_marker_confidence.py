# Generated by Django 5.1.7 on 2025-04-07 21:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='marker',
            name='confidence',
            field=models.IntegerField(default=100),
        ),
    ]
