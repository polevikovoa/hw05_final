# Generated by Django 2.2.19 on 2023-01-30 18:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0004_auto_20230130_1334'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='text',
            field=models.TextField(blank=True, max_length=200, verbose_name='Описание поста'),
        ),
    ]
