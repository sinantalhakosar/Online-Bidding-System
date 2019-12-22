from djongo import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class AuctionUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_verified = models.BooleanField(default=False, blank=True)
    verification_code = models.CharField(max_length=100, blank=True)
    balance = models.IntegerField(blank=True, default=0)
    reservedbalance = models.IntegerField(blank=True, default=0)

    def __str__(self):
        return self.user.username

    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            AuctionUser.objects.create(
                user=instance, verification_code=instance.username)

    @receiver(post_save, sender=User)
    def save_user_profile(sender, instance, **kwargs):
        instance.auctionuser.save()


class Item(models.Model):
    BID_TYPE = (
        ('I', 'Increment'),
        ('II', 'Instant-Increment'),
        ('D', 'Decrement'),
    )
    owner = models.CharField(max_length=100)
    newowner = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    price = models.IntegerField(blank=True)
    title = models.CharField(max_length=100, unique=True)
    itemtype = models.CharField(max_length=100)
    description = models.CharField(max_length=100)
    bidtype = models.CharField(max_length=2, choices=BID_TYPE)
    starting = models.IntegerField(blank=True)
    minbid = models.IntegerField()
    image = models.CharField(max_length=100, blank=True)
    stopbid = models.IntegerField(blank=True)
    currentbid = models.IntegerField(blank=True)
    lastbidder = models.CharField(max_length=100, blank=True)
    decremented = models.IntegerField(blank=True)
    period = models.IntegerField(blank=True, default=1)
    delta = models.IntegerField(blank=True, default=10)
    stop = models.IntegerField(blank=True, default=0)

    def __str__(self):
        return self.owner


class Notification(models.Model):
    userid = models.IntegerField()
    message = models.CharField(max_length=100)
    isread = models.BooleanField(default=False)

    def __str__(self):
        return self.message


class History(models.Model):
    itemid = models.IntegerField()
    historytype = models.CharField(max_length=100)
    title = models.CharField(max_length=100)
    issold = models.BooleanField(default=False)
    soldto = models.CharField(max_length=100)
    bidder = models.CharField(max_length=100)
    bidamount = models.IntegerField()

    def __str__(self):
        return self.historytype
