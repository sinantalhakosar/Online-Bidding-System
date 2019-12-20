from django.shortcuts import redirect, render
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.views.generic import *
from django.urls import reverse_lazy, reverse
from .models import *
from .forms import *
from django.http import JsonResponse


def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
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
        print(self.request.user.username)
        return Item.objects.filter(owner=self.request.user.username)


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


class AddItem(CreateView):
    form_class = ItemForm
    success_url = reverse_lazy('home')
    template_name = 'newitem.html'

    def get_success_url(self):
        self.object.owner = self.request.user.username
        self.object.state = "onhold"
        self.object.price = 0
        if(self.object.minbid < self.object.starting):
            self.object.minbid = self.object.starting
        self.object.save()
        return reverse('home')


def startauction(request):
    body = request.POST
    print(body)
    itemid = body.__getitem__("itemid")
    item = Item.objects.get(id=int(itemid))
    stopbid = body.__getitem__("stopbid")
    print(itemid)
    print(stopbid)
    response = {}
    if (stopbid == ""):
        item.state = "active"
        item.save()
        response['msg'] = "The auction had started"
        return JsonResponse(response)
    else:
        if(int(stopbid) < item.minbid):
            response['msg'] = "Stop bid can not be less than min bid"
            return JsonResponse(response)
        else:
            item.state = "active"
            item.stopbid = int(stopbid)
            item.save()
            response['msg'] = "The auction had started"
            return JsonResponse(response)
