from django.shortcuts import redirect, render
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.views.generic import *
from django.urls import reverse_lazy, reverse
from .models import *
from .forms import *
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.db.models import Q
from .tasks import *


def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(
                request, 'Your password was successfully updated!')
            return redirect('home')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'accounts/change_password.html', {
        'form': form
    })


class HomePageView(ListView):
    template_name = 'home.html'
    context_object_name = 'items'

    def get_queryset(self):
        return Item.objects.filter(Q(owner=self.request.user.username) | Q(newowner=self.request.user.username))


class MarketView(ListView):
    template_name = 'market.html'
    context_object_name = 'items'

    def get_queryset(self):
        return Item.objects.filter(state="active").exclude(owner=self.request.user.username)


class SignUp(CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'


def verify(request):
    body = request.POST
    verification_code = body.__getitem__("verification_code")
    if(verification_code == request.user.username):
        user = request.user
        user.auctionuser.is_verified = True
        user.save()
    return redirect('home')


def addbalance(request):
    body = request.POST
    amount = body.__getitem__("amount")
    user = request.user
    user.auctionuser.balance += int(amount)
    user.save()
    response = {}
    response['msg'] = "Your new balance is {0}".format(
        user.auctionuser.balance)
    return JsonResponse(response)


class AddItem(CreateView):
    form_class = ItemForm
    success_url = reverse_lazy('home')
    template_name = 'newitem.html'

    def get_success_url(self):
        self.object.owner = self.request.user.username
        self.object.state = "onhold"
        self.object.price = 0
        self.object.currentbid = 0
        self.object.stopbid = 0
        self.object.decremented = self.object.starting
        self.object.save()
        return reverse('home')


def startauction(request):
    body = request.POST
    itemid = body.__getitem__("itemid")
    item = Item.objects.get(id=int(itemid))
    stopbid = body.__getitem__("stopbid")
    response = {}
    if(item.state == "active"):
        response['msg'] = "The auction already started"
        return JsonResponse(response)
    if(item.state == "sold"):
        response['msg'] = "This item is already sold"
        return JsonResponse(response)
    else:
        if (stopbid == ""):
            item.state = "active"
            item.save()
            if item.bidtype == "D":
                decrementer(item.id, repeat=item.period * 60)
            response['msg'] = "The auction had started"
            return JsonResponse(response)
        else:
            if(int(stopbid) < item.starting):
                response['msg'] = "Stop bid can not be less than starting bid"
                return JsonResponse(response)
            else:
                item.state = "active"
                item.stopbid = int(stopbid)
                item.save()
                response['msg'] = "The auction had started"
                return JsonResponse(response)


def sellitem(request):
    body = request.POST
    itemid = body.__getitem__("itemid")
    item = Item.objects.get(id=int(itemid))
    response = {}
    if (item.lastbidder == ""):
        item.state = "onhold"
        item.save()
        response['msg'] = "This item is not sold anyone because there is no bidder, its state is now onhold."
        return JsonResponse(response)
    if (item.state == "sold"):
        response['msg'] = "You cannot sell already solded item."
        return JsonResponse(response)
    item.price = item.currentbid
    newowner = User.objects.get(username=item.lastbidder)
    item.newowner = item.lastbidder
    item.state = "sold"
    newowner.auctionuser.balance -= item.currentbid
    newowner.auctionuser.reservedbalance -= item.currentbid
    item.save()
    newowner.save()
    History.objects.create(itemid=item.id,
                           historytype="Sell Item",
                           title=item.title,
                           issold=True,
                           soldto=item.newowner)
    response['msg'] = "Item is sold for {0} and the new owner is {1}".format(
        item.price, newowner.user.username)
    return JsonResponse(response)


def bid(request):
    body = request.POST
    bidamount = body.__getitem__("bidamount")
    user = request.user
    itemid = body.__getitem__("itemid")
    item = Item.objects.get(id=int(itemid))
    amount = int(bidamount)
    response = {}
    if(item.state == "active"):
        if(item.bidtype == "I"):
            if amount >= item.currentbid+item.minbid:
                if(user.auctionuser.balance - user.auctionuser.reservedbalance >= amount):
                    if(item.stopbid != 0 and amount >= item.stopbid):
                        item.price = amount
                        item.lastbidder = user.username
                        item.currentbid = amount
                        item.newowner = user.username
                        item.state = "sold"
                        user.auctionuser.balance -= amount
                        item.save()
                        user.save()
                        History.objects.create(itemid=item.id,
                                               historytype="Sell Item",
                                               title=item.title,
                                               issold=True,
                                               soldto=item.newowner)
                        response['msg'] = "Item is sold for {0} and the new owner is {1}".format(
                            item.price, user.username)
                        return JsonResponse(response)
                    else:
                        if(amount > item.currentbid):
                            item.currentbid = amount
                            if (item.lastbidder != ""):
                                lastbidder = User.objects.filter(
                                    username=item.lastbidder)
                                lastbidder.auctionuser.reservedbalance -= amount
                                lastbidder.save()
                            item.lastbidder = user.username
                            user.auctionuser.reservedbalance += amount
                            item.save()
                            user.save()
                            History.objects.create(itemid=item.id,
                                                   historytype="New Bid",
                                                   title=item.title,
                                                   issold=False,
                                                   bidder=item.lastbidder,
                                                   bidamount=amount)
                            response['msg'] = "The new bid for {0} is {1}$".format(
                                item.title, item.currentbid)
                            return JsonResponse(response)
                        else:
                            response['msg'] = "Your bid need to more than last bid"
                            return JsonResponse(response)
                else:
                    response['msg'] = "You don't have enough amount to bid to this item"
                    return JsonResponse(response)
            else:
                response['msg'] = "You can not bid less than min bid"
                return JsonResponse(response)
        elif(item.bidtype == "D"):
            if(user.auctionuser.balance - user.auctionuser.reservedbalance >= amount):
                if(amount >= item.decremented):
                    item.price = amount
                    item.newowner = user.username
                    item.state = "sold"
                    user.auctionuser.balance -= amount
                    item.save()
                    user.save()
                    History.objects.create(itemid=item.id,
                                           historytype="Sell Item",
                                           title=item.title,
                                           issold=True,
                                           soldto=item.newowner)
                    response['msg'] = "Item is sold for {0} and the new owner is {1}".format(
                        item.price, user.username)
                    return JsonResponse(response)
                else:
                    response['msg'] = "Your bid need to more than decremented value"
                    return JsonResponse(response)
            else:
                response['msg'] = "You don't have enough amount to bid to this item"
                return JsonResponse(response)
        elif(item.bidtype == "II"):
            if(user.auctionuser.balance - user.auctionuser.reservedbalance >= amount):
                if(item.stopbid != 0 and amount+item.currentbid >= item.stopbid):
                    item.price = amount
                    item.newowner = user
                    item.state = "sold"
                    user.auctionuser.balance -= amount
                    item.save()
                    user.save()
                    History.objects.create(itemid=item.id,
                                           historytype="Sell Item",
                                           title=item.title,
                                           issold=True,
                                           soldto=item.newowner)
                    response['msg'] = "Item is sold for {0} and the new owner is {1}".format(
                        item.price, user.username)
                    return JsonResponse(response)
                else:
                    item.currentbid += amount
                    item.lastbidder = user
                    user.auctionuser.balance -= amount
                    user.save()
                    item.save()
                    History.objects.create(itemid=item.id,
                                           historytype="New Bid",
                                           title=item.title,
                                           issold=False,
                                           bidder=item.lastbidder,
                                           bidamount=amount)
                    response['msg'] = "The new bid for {0} is {1}$".format(
                        item.title, item.currentbid)
                    return JsonResponse(response)
            else:
                response['msg'] = "You don't have enough amount to bid to this item"
                return JsonResponse(response)
    else:
        response['msg'] = "This item is not on sale"
        return JsonResponse(response)


def notify(request):
    user = request.user
    notifications = Notification.objects
    response = {}
    response['msg'] = []
    for e in Notification.objects.filter(userid=user.id, isread=False):
        e.isread = True
        e.save()
        response['msg'].append(e.message)
    return JsonResponse(response)


def watch(request):
    body = request.POST
    itemtype = body.__getitem__("itemtype")
    user = request.user
    if(itemtype == ""):
        notify_user(user.id)
    else:
        notify_user(user.id, itemtype)
    response = {}
    response['msg'] = "You are now watching {0}".format(itemtype)
    return JsonResponse(response)


def watchselected(request):
    body = request.POST
    itemid = body.__getitem__("itemid")
    item = Item.objects.get(id=int(itemid))
    user = request.user
    notify_user_item(user.id, int(itemid))
    response = {}
    response['msg'] = "You are now watching {0}".format(item.title)
    return JsonResponse(response)


def history(request):
    body = request.POST
    itemid = body.__getitem__("itemid")
    user = request.user
    notify_user_item(user.id, int(itemid))
    response = {}
    response['msg'] = []
    for e in History.objects.filter(itemid=int(itemid)):
        response['msg'].append(e)
    return JsonResponse(response)
