from django import forms 
from .models import *
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


class RegistrationForm(forms.ModelForm):
    user_name = forms.CharField(
        label='Username', min_length=4, max_length=50, help_text='Required', widget=forms.TextInput(
            attrs={'class': 'form-control'}
        )
    ) 
    email = forms.EmailField(
       max_length=100, help_text='Required', error_messages={'required':'You will need an email address'}, widget=forms.EmailInput(
            attrs={'class': 'form-control'}
        ) 
    )
    full_name = forms.CharField(
        label='Full Name', min_length=4, max_length=50, help_text='Required', widget=forms.TextInput(
            attrs={'class': 'form-control'}
        )
    ) 
    password1 = forms.CharField(
        label='Password', widget=forms.PasswordInput(
            attrs={'class':'form-control'}
        )
    )
    password2 = forms.CharField(
        label='Confirm Password', widget=forms.PasswordInput(
            attrs={'class':'form-control'}
        )
    )

    class Meta:
        model = User
        fields = ('user_name', 'email', 'full_name')
        

    def clean_username(self):
        user_name = self.cleaned_data['user_name'].lower()
        r = User.objects.filter(user_name=user_name)
        if r.count():
            raise forms.ValidationError("Username already exist")
        return user_name
    
    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if not password1:
            raise forms.ValidationError('Password is required.')
        try:
            validate_password(password1, self.instance)
        except ValidationError as e:
            raise forms.ValidationError("\n".join(e.messages))
        return password1

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Passwords do not match.')
        return password2
    
    def save(self, commit=True):
        user = super(RegistrationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user
    

class LoginForm(forms.Form):

    email = forms.EmailField(label="Email Address*", widget=forms.EmailInput(attrs={'class':'form-control'}))
    password = forms.CharField(label="Password*", widget=forms.PasswordInput(attrs={'class':'form-control'}))


