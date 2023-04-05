from django import forms
from .models import Stock
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User

class StockForm(forms.Form):
    symbol = forms.CharField(max_length=10)
    quantity = forms.IntegerField(min_value=1)
    transaction_price = forms.FloatField(min_value=0.001)


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True,max_length=45, help_text='Inform a valid email address.')
    username = forms.CharField(required=True,max_length=30, help_text='Create a username')
    password1 = forms.CharField(required=True,max_length=30, help_text='Create a password',widget=forms.PasswordInput)
    password2 = forms.CharField(required=True,max_length=30, help_text='Re-type password',widget=forms.PasswordInput)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', )
        labels = {'password1':'','password2':''}

class LoginForm(AuthenticationForm):
    pass   