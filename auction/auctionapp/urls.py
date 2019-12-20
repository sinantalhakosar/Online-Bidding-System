from django.urls import include, path

from . import views

urlpatterns = [
    path('', views.HomePageView.as_view(), name='home'),
    path('signup/', views.SignUp.as_view(), name='signup'),
    path('verify/', views.verify, name="verify"),
    path('additem/', views.AddItem.as_view(), name="newitem"),
    path('market/', views.AddItem.as_view(), name="market"),

]
