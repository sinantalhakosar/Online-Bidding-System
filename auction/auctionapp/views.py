from django.shortcuts import redirect
from django.contrib.auth.forms import UserCreationForm
from django.views.generic import *
from django.urls import reverse_lazy, reverse
from .models import *
from .forms import *


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
        self.object.save()
        return reverse('home')
