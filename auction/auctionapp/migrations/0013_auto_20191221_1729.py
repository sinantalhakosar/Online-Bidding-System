# Generated by Django 2.2.8 on 2019-12-21 17:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('auctionapp', '0012_auto_20191221_1721'),
    ]

    operations = [
        migrations.RenameField(
            model_name='history',
            old_name='userid',
            new_name='itemid',
        ),
    ]
