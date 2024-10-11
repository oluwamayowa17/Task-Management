from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from .forms import RegistrationForm, LoginForm
from .models import *
from django.utils.safestring import mark_safe
from .token import account_activation_token, collaborator_token

from django.conf import settings
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage
import json

# Create your views here.
def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except:
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.is_staff = True
        user.save()

        messages.success(request, 'Thank you for email confirmaton, you can now login your account')
        return redirect('taskapp:user_login')
    else:
        messages.error(request, 'Activation link invalid!')

    return redirect('/')


def activateEmail(request, user, to_email):
    mail_subject = 'Activate Your Account'
    mail_message = render_to_string('mail-template.html', {
        'user': user.user_name,
        'domain': get_current_site(request).domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
        'protocol': "https" if request.is_secure() else "http"
    })
    email = EmailMessage(mail_subject, mail_message, to=[to_email])
    if email.send():
        message = mark_safe(
            f'Dear <b>{user}</b>, in order to complete registration, check your email @ <b>{to_email}</b>\
            and click on the activation link that was sent. <b>Note:</b> Check your spam folder.'
        )
        messages.success(request, message)
    else:
        message.error(request, f'Problem sending email to {to_email}, check if you typed it correctly')

def regiter(request):
    if request.method == "POST":
        register = RegistrationForm(request.POST)
        if register.is_valid():
            user = register.save(commit=False)
            user.is_active = False
            user.save()
            activateEmail(request, user, register.cleaned_data.get('email'))
        else:
            for error in list(register.errors.values()):
                messages.error(request, error)
    else:
        register = RegistrationForm()
    context = {'reg': register}
    return render(request, 'register.html', context)

def user_login(request):
    if request.method == "POST":
        user_log = LoginForm(request.POST)
        if user_log.is_valid():
            email = user_log.cleaned_data['email']
            password = user_log.cleaned_data['password']
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('taskapp:dashboard')
            else:
                messages.error(request, 'Email or password Incorrect')
    else:
        user_log = LoginForm()
    return render(request, 'login.html', {'login': user_log})

def user_logout(request):
    logout(request)
    return redirect('account:user_login')
