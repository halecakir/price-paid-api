from django.contrib.auth.models import User
from django.db import models
from django_cte import CTEManager


class Property(models.Model):
    objects = CTEManager()
    postal_code = models.CharField(max_length=50)
    property_type = models.CharField(max_length=1)
    price = models.IntegerField()
    transfer_date = models.DateTimeField()

    def __str__(self):
        return self.postal_code
