from django.urls import path
from account import views

app_name = 'account'

urlpatterns = [
    path('register/', views.regiter, name='register'),
    path('login/', views.user_login, name='user_login'),
    path('logout/', views.user_logout, name='user_logout'),
    path('activate/<uidb64>/<token>', views.activate, name='activate'),

]