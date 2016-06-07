from __future__ import unicode_literals

from django.db import models


# Create your models here.
class Post(models.Model):
    content = models.TextField()
    type = models.CharField(max_length=50)
    time = models.BigIntegerField()
    cid = models.IntegerField()
    did = models.IntegerField() # in case of model it would be a foreign key
    pid = models.IntegerField()
    user = models.CharField(max_length=50)
    evaluated = models.BooleanField(default=False)


