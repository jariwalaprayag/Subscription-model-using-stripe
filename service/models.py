from django.db import models
from django.contrib.auth.models import User


class Service(models.Model):
    name = models.CharField(max_length=100)
    charges = models.FloatField()


class Subscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    state = models.CharField(max_length=255, default="not active")
    stripeid = models.CharField(max_length=255)
    stripe_subscription_id = models.CharField(max_length=255)
    cancel_at_period_end = models.BooleanField(default=False)
    membership = models.BooleanField(default=False)

# Create your models here.
