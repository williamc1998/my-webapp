import yfinance as yf
import pandas as pd
import numpy as np
from django.shortcuts import render
import sys
import os
from django.http import HttpResponseRedirect,JsonResponse
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.views import View
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib import messages
from metatracker.models import Stock,Timings
from metatracker.forms import StockForm
import decimal
from datetime import date, timedelta
import random
import websocket, requests
import finnhub
from newsapi import NewsApiClient
from alpha_vantage.timeseries import TimeSeries
import datetime

# here are two basic api+calculate functions
def price_grabber(ticker):
    ticker = yf.Ticker(ticker)
    print(ticker.fast_info)
    return ticker.fast_info.last_price

def value_calc(count,ticker):
    price = price_grabber(ticker)
    value = count*price
    return value


# def get_news_newsapi(symbols):
#     today = date.today().strftime('%Y-%m-%d')
#     yesterday = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
#     newsapi = NewsApiClient(api_key=)
#     print(''.join([symbol + ' OR ' for symbol in symbols])[:-4])
#     headline = newsapi.get_everything(q=''.join([symbol + 'OR' for symbol in symbols])[:2],
#                                       from_param=yesterday,
#                                       to=today,
#                                       language='en',
#                                       sources='google-news',
#                                       sort_by='relevancy')
#     print('newsapiheadlines:',headline)

# def price_grabber(ticker):
#     ts = TimeSeries(key='7MMWRT0WF76LHW65',output_format='pandas')
#     data, meta_data = ts.get_intraday(ticker,interval='1min',outputsize='compact')
#     data = data['4. close'].iloc[0]
#     print(data)
#     print(meta_data)
#     return data


    
    
# def get_news_av(symbols):
    
    
def update(request):
    stocks = Stock.objects.filter(user=request.user)
    prices = {}
    all_value = 0
    for i,stock in enumerate(stocks):
        share_price = price_grabber(stock.symbol)
        stock_value = round(stock.quantity * share_price,2)
        all_value += stock_value
        profit = (share_price*stock.quantity) - (stock.accumulated_spend)
        profit_percentage = profit/stock.accumulated_spend*100
        stock.profit_value = round(profit,2)
        stock.profit_percentage = round(profit_percentage,2)
        stock.updated_price = round(share_price,2)
        if profit_percentage >= 0:
            stock.is_profit = True
        else:
            stock.is_profit = False
            stock.profit_value = round(abs(profit),2)
        prices[stock.symbol] = share_price
        print('CURRENT PRICE:',share_price)
        stock.total_value = round(value_calc(stock.quantity,stock.symbol),2)
        stock.save()
    all_value = round(all_value,2)
    stocks = Stock.objects.filter(user=request.user)
    return stocks,all_value


# here is the function to provide the new stock value
def process_form(request):
    form = StockForm(request.POST)
    if form.is_valid():
        print('valid form')
        symbol=form.cleaned_data['symbol'].upper()
        try:
            price_grabber(symbol)
            failed = False
        except:
            print('failed to grab price')
            failed = True
            return HttpResponseRedirect('.')
        if failed == False:
            new_quantity=form.cleaned_data['quantity']
            new_buy_price=form.cleaned_data['transaction_price']
            stock, created = Stock.objects.get_or_create(symbol=symbol, user=request.user)
            old_quantity = stock.quantity
            total_quantity = stock.quantity + new_quantity
            stock.quantity = total_quantity
            stock.average_buy_price = round(((new_buy_price*new_quantity) + (stock.average_buy_price*old_quantity))/stock.quantity,2)
            stock.accumulated_spend += (new_quantity*new_buy_price)
            share_price = price_grabber(symbol)
            stock.total_value = round(value_calc(total_quantity, symbol),2)
            stock.updated_price = round(share_price,2)
            profit = (share_price*stock.quantity) - (stock.accumulated_spend)
            profit_percentage = profit/stock.accumulated_spend*100
            stock.profit_percentage = round(profit_percentage,2)
            stock.save()

    else:
        print('invalid form')
    return HttpResponseRedirect('.')

# def get_news(request):
#     stocks = Stock.objects.filter(user=request.user)
#     news_objects = {}
#     if len(stocks) > 4:
#         count = 0
#         while count < 6:
#             for i,stock in enumerate(stocks):
#                 obj = yf.Ticker(stock.symbol)
#                 print('STARTING NEWS SCRAPE')
#                 news_objects[stock.symbol]=[obj.news[i]['title'],obj.news[i]['link']]
#                 count+=1
#                 if count >=6:
#                     break
#     else:
#         try:
#             for i,stock in enumerate(stocks):
#                 print(stock.symbol)
#                 obj = yf.Ticker(stock.symbol)
#                 news_objects[stock.symbol]=[obj.news[0]['title'],obj.news[0]['link']]
                
#         except:
#             obj = yf.Ticker('SPY')
#             news_objects['SPY']=[obj.news[0]['title'],obj.news[0]['link']]
#     print(news_objects)
#     return news_objects

def get_news(request):
    from collections import defaultdict
    stocks = Stock.objects.filter(user=request.user)
    timings = Timings.objects.get_or_create(user=request.user)
    key = os.getenv('av_key')
    news_obj = {}
    values = {}
    for i,stock in enumerate(stocks):
        try:
            values[stock.symbol] = stock.total_value
            url = f'https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={stock.symbol}&limit=5&sort=RELEVANCE&apikey={key}'
            print(url)
            r = requests.get(url)
            data = r.json()
            relevant = []
            for i in range(len(data['feed'])):
                match = data['feed'][i]['ticker_sentiment'][0]['ticker']
                if match == stock.symbol:
                    relevant.append(data['feed'][i])
                relevant = relevant[:35]
            pairs = []
            for i, j in enumerate(relevant):
                pairs.append([j['title'],j['url']])
                news_obj[stock.symbol] = pairs
        except:
            continue

    master = defaultdict(list)
    for i in range(4):
        choice_stock = random.choice(list(news_obj.keys()))
        choice_pair = random.choice(news_obj[choice_stock])
        master[choice_stock].append(choice_pair)
    values = {k: v for k, v in sorted(values.items(), key=lambda item: item[1])}
    print('values:',values)
    return master


def get_earnings(request):
    stocks = Stock.objects.filter(user=request.user)
    finnhub_client = finnhub.Client(api_key=os.getenv('fh_key'))
    dates = {}
    for i,stock in enumerate(stocks):
        try:
            calendar = finnhub_client.earnings_calendar(_from=datetime.date.today(), to=datetime.date.today()+datetime.timedelta(days=95), symbol=f'{stock.symbol}', international=False)
            date = calendar['earningsCalendar'][0]['date']
            dates[f'{stock.symbol}'] = date
        except:
            continue
    print(dates)
    sorted_dates_keys = sorted(dates, key=dates.get)
    print(sorted_dates_keys)
    sorted_dates_keys = sorted_dates_keys[:3]
    dates = {key:dates[key] for key in sorted_dates_keys}
    print(dates)
    return dates
    

# here stocks will be displayed
def display_stocks(request):
    if Stock.objects.filter(user=request.user).exists():
        # this is causing double run through of update. please fix.
        stocksAndValue=update(request)
        stocks = stocksAndValue[0]
        all_value=round(stocksAndValue[1],2)
        form = StockForm()
        try:
            news_object = dict(get_news(request))
        except:
            pass
        try:
            news_object
        except:
            news_object = {}
        earnings = get_earnings(request)
        print(type(news_object))
        print(news_object)
        stock_arrays = list(stocks.values())
        total_vals = []
        names = []
        yearly_changes = []
        symbols = []
        for stock in stocks:
            total_vals.append(stock.total_value)
            names.append(stock.symbol)
            ticker = yf.Ticker(stock.symbol)
            year_change = round((ticker.fast_info.year_change)*100,2)
            print('year change:',year_change)
            yearly_changes.append(year_change)
            symbols.append(stock.name)
        
        return render(request, 'htmlfile.html', {'form': form, 'stocks': stocks,
                                                'all_value':all_value,
                                                'news_object':news_object,
                                                'total_vals':total_vals,
                                                'names':names,
                                                'yearly_changes':yearly_changes,
                                                'earnings_dates':earnings})
