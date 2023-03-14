from django.urls import path,include
import sys
sys.path.append("/Users/william/desktop/web/metasite_root")
from metatracker import views
from django.contrib import admin
from django.conf import settings
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls,name='admin'),
    path('home/', views.home_view, name='home'),
    path('portfolio/',views.portfolio_view, name='portfolio'),
    path('signup/', views.signup.as_view(), name='signup'),
    #path('login-view/', views.login_view, name='login-view'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('__debug__/', include('debug_toolbar.urls')),
    path('logout/', views.logout_view, name='logout'),
    path('delete',views.delete,name='delete')]