# urls.py
from django.urls import path
from . import views

app_name = 'collab'

urlpatterns = [
    path('accept-invitation/uid/<uidb64>/token/<token>/', views.accept_invitation, name='accept-invitation'),
]