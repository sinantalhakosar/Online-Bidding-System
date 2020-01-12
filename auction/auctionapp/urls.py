from django.urls import include, path
from django.conf.urls import url

from . import views

urlpatterns = [
    path('', views.HomePageView.as_view(), name='home'),
    path('signup/', views.SignUp.as_view(), name='signup'),
    path('verify/', views.verify, name="verify"),
    path('additem/', views.AddItem.as_view(), name="newitem"),
    path('market/', views.MarketView.as_view(), name="market"),
    path('startauction/', views.startauction, name="startauction"),
    path('sellitem/', views.sellitem, name="sellitem"),
    path('addbalance/', views.addbalance, name="addbalance"),
    path('bid/', views.bid, name="bid"),
    path('notify/', views.notify, name="notify"),
    path('readnotify/', views.readnotify, name="readnotify"),
    path('watch/', views.watch, name="watch"),
    path('watchselected/', views.watchselected, name="watchselected"),
    path('history/', views.history, name="history"),
    path('report/', views.report, name="report"),
    path('getUserItems/', views.getUserItems, name="getUserItems"),
    path('getMarketItems/', views.getMarketItems, name="getMarketItems"),
    url(r'^password/$', views.change_password, name='change_password'),
]
