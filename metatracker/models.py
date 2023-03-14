from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
import os
import sys
# sys.path.append("/Users/william/desktop/web/metasite_root")
os.environ['DJANGO_SETTINGS_MODULE'] = 'metasite.settings'

# Create your models here.
class Stock(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,default=1)
    symbol = models.CharField(max_length=10)
    name = models.CharField(max_length=50)
    quantity = models.PositiveIntegerField(default=0.0)
    average_buy_price = models.FloatField(default=0.0)
    updated_price = models.FloatField(default=0.0)
    total_value = models.FloatField(default=0.0)
    accumulated_spend = models.FloatField(default=0.0)
    profit_percentage = models.FloatField(default=0.0)
    profit_value = models.FloatField(default=0.0)
    is_profit = models.BooleanField(default=False)
    class Meta:
        unique_together = ['symbol', 'user']
    def __str__(self):
        return self.name


class Listed(models.Model):
    symbol = models.CharField(max_length=10)
    last_price = models.FloatField(default=0.0)
    price_yesterday = models.FloatField(default=0.0)
    price_last_week = models.FloatField(default=0.0)
    price_last_month = models.FloatField(default=0.0)
    price_three_month = models.FloatField(default=0.0)
    price_six_month = models.FloatField(default=0.0)
    class Meta:
        app_label  = 'metatracker'
    def __str__(self):
        return self.name

class Timings(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,default=1)
    last_news_time = models.DateTimeField(auto_now=True)
    
    
class StockTracker(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,default=1)
    symbol = models.CharField(max_length=10)
    total_quantity = models.PositiveIntegerField(default=0.0)
    avg_buy_price = models.DecimalField(max_digits=5, decimal_places=2,default=0.0)
    
    
