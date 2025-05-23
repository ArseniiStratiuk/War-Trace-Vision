# Generated by Django 5.1.7 on 2025-04-28 14:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('detection', '0002_detection_metadata_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='detection',
            name='processed_image',
            field=models.FileField(blank=True, null=True, upload_to='detection_results/'),
        ),
        migrations.AlterField(
            model_name='detection',
            name='image_path',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
