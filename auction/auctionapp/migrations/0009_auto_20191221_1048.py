# Generated by Django 2.2.8 on 2019-12-21 10:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auctionapp', '0008_auto_20191221_1033'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='lastbidder',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='item',
            name='newowner',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='item',
            name='owner',
            field=models.CharField(max_length=100),
        ),
    ]
