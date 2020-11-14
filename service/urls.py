from django.contrib import admin
from django.urls import path, reverse, re_path
from . import views
from .views import Login, Logout, Product, User_service, CheckOut, Cancel, Restart
from django_registration.backends.one_step.views import RegistrationView

urlpatterns = [
    path(
        'register/',
        RegistrationView.as_view(success_url='home'),
        name='registeration'
    ),
    path(
        'home/', views.home, name='home'
    ),
    path(
        'register/home', views.home, name='home'
    ),
    re_path(
        r'.*login/',
        Login.as_view(),
        name='login'
    ),
    path(
        'logout/',
        Logout.as_view(),
        name='logout'
    ),
    path(
        'product/',
        Product.as_view(),
        name='product'
    ),
    path(
        'service/',
        User_service.as_view(),
        name='service'
    ),
    path(
        'checkout/',
        CheckOut.as_view(),
        name='checkout'
    ),
    re_path(
        r'.*cancel/',
        Cancel.as_view(),
        name='cancel'
    ),
    re_path(
        r'.*restart/',
        Restart.as_view(),
        name='restart'
    ),
]
