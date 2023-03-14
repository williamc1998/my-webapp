from django.shortcuts import render
import sys
import os
from math import sqrt
from django.http import HttpResponseRedirect,JsonResponse
from rest_framework import status

from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.views.generic.edit import FormView
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from .forms import SignUpForm, LoginForm
from django.views import View
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib import messages
from metatracker.models import Stock
from metatracker.forms import StockForm
from django.contrib.auth.forms import AuthenticationForm
import decimal
import yfinance as yf
import requests
from django.conf import settings
from django.urls import reverse


# sys.path.append("/Users/william/desktop/web/metasite_root")


def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'


# Create your views here.
@login_required(login_url='login')
def portfolio_view(request):
    if request.user.is_authenticated:
        from metatracker.apicaller import process_form, get_news,display_stocks,price_grabber,value_calc
        if request.method == 'POST':
            return process_form(request)
        else:
            if  Stock.objects.filter(user=request.user).exists():
                stocks = Stock.objects.filter(user=request.user)
                if is_ajax(request=request):
                    print('is ajax!')
                    prices = {}
                    for stock in stocks:
                        share_price = price_grabber(stock.symbol)
                        stock.updated_price = share_price
                        prices[stock.symbol] = share_price
                        stock.total_value = round(value_calc(stock.quantity,stock.symbol),2)
                        stock.save()
                    all_value = 0
                    profit_percentage = 0
                    stocks = Stock.objects.filter(user=request.user) 
                    for i,stock in enumerate(stocks):
                        share_price = price_grabber(stock.symbol)
                        stock_value = round(stock.quantity * share_price,2)
                        all_value += stock_value
                        profit = round((share_price*stock.quantity) - (stock.accumulated_spend),2)
                        profit_percentage = round(profit/stock.accumulated_spend*100,2)
                        stock.profit_value = round(profit,2)
                        stock.profit_percentage = profit_percentage
                        if profit_percentage >= 0:
                            stock.is_profit = True
                        else:
                            stock.is_profit = False
                        stock.save()
                    stocks = Stock.objects.filter(user=request.user)
                    data = {'stocks': list(stocks.values()),
                            'all_value': round(all_value,2),
                            'pp':profit_percentage,}
                    print(data)                    
                    return JsonResponse(data,safe=False)
                else:
                        return display_stocks(request)
            else:
                stocks = Stock.objects.filter(user=request.user)
                form = StockForm(request.POST)
                return render(request,'htmlfile.html',{'form':form,'stocks':stocks})
    else:
        return redirect('login')

# reset button
# @api_view(['GET', 'POST'])
def delete(request):
    from metatracker.models import Stock
    for object in Stock.objects.filter(user=request.user):
        object.delete()
    print('deleted')
    return Response("YOUR TEXT HERE")


# signup and log in
class signup(View):
    from .forms import SignUpForm
    form_class = SignUpForm
    template_name = 'signup.html'

    def get(self, request):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            print('valid form')
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            # Check if a user with the same username already exists
            if User.objects.filter(username=username).exists():
                form.add_error("username", "A user with this username already exists.")
                return render(request, self.template_name, {'form': form})
            else:
                print('user doesnt yet exist, so creating')
                user = User.objects.create_user(username=username, password=raw_password)
                user.set_password(raw_password)
                user.save()
                print(user,' created')
                print(request, f"Account created for {user.username}!")
                print(user.password,user.username)
                return HttpResponseRedirect('/login/')
        else:
            for field in form:
                for error in field.errors:
                    messages.error(request, error)
            print('not valid')
            print(form.errors)
        return render(request, self.template_name, {'form': form})


class LoginView(View):
    success_url = reverse_lazy('home')
    template_name = 'login.html'

    def get(self, request, *args, **kwargs):
        form = AuthenticationForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = AuthenticationForm(request=request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            print(request.user)
            if user is not None:
                print('user is not None!:)')
                login(request, user)
                print('logged in!')
                return redirect(self.get_success_url())
        else:

            print('form not valid')
            print(form.errors)
        return render(request, self.template_name, {'form': form})

    def get_success_url(self):
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        else:
            return reverse_lazy('home')


def logout_view(request):
    print('attempting logout')
    logout(request)
    print('logged out')
    if 'next' in request.session:
        del request.session['next']
    return redirect('home')
# class LoginView(FormView):
#     form_class = LoginForm
#     template_name = 'login.html'
#     success_url = reverse_lazy('home')
    
#     def form_valid(self, form):
#         print(form.cleaned_data)
#         # authenticate user
#         username = form.cleaned_data.get('username')
#         password = form.cleaned_data.get('password')
#         user = authenticate(self.request, username=username, password=password)
#         # check if user is authenticated
#         if user is not None:
#                 login(self.request, user)
#                 print(user,'logged in')
#                 messages.success(self.request, f'{user} logged in')
#               #  next_url = self.request.POST.get('next') or self.request.GET.get('next')
#                 return redirect('/home/')
#         else:
#             messages.error(self.request, 'Invalid login credentials')
#             print('invalid credentials at login')
#             return self.form_invalid(form)
        
#     def get_success_url(self):
#          # redirect to next url if it exists, otherwise redirect to the default success url
#         next_url = self.request.POST.get('next') or self.request.GET.get('next')
#         if next_url:
#             return next_url
#         return super().get_success_url()




@login_required(login_url='login')
def home_view(request):
    if request.user.is_authenticated:
        print(request.user)
    else:
        print('no auth')
    return render(request, 'frontpage.html')


# update data every 30 seconds without having to refresh page
def updated_data(request):
    stocks = Stock.objects.filter(user=request.user)
    total_value = 0
    for stock in stocks:
        stock_value = stock.quantity * stock.price
        total_value += stock_value
    data = {'stocks': stocks, 'total_value':total_value}
    return JsonResponse(data)