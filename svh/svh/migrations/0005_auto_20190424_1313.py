# Generated by Django 2.2 on 2019-04-24 10:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('svh', '0004_auto_20190424_1312'),
    ]

    operations = [
        migrations.AlterField(
            model_name='videofile',
            name='source',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='svh.VideoSource'),
        ),
    ]
