# Generated by Django 2.2.8 on 2019-12-20 13:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('auctionapp', '0004_auctionuser_user'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='auctionuser',
            name='email',
        ),
    ]
