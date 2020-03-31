from django.db import models
from django.contrib.postgres.fields import JSONField


# Create your models here.
from dapp1.utils import randomstring


class Location(models.Model):
    name = models.TextField()
    uid = models.CharField(max_length=220,unique = True,editable = False)
    data = JSONField(default={'name': 'test'})

    def __str__(self):
        return self.name

    def save(self, *args):
        self.uid = randomstring(12)
        return super(Location, self).save(*args)


class Group(models.Model):
    name = models.TextField(unique=True)
    uid = models.CharField(max_length=220, unique=True, editable=False)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True)
    data = JSONField(default={'name': 'test'})
    def __str__(self):
        return self.name

    def save(self, *args):
        self.uid = randomstring(12)
        return super(Group, self).save(*args)


class User(models.Model):
    name = models.TextField()
    uid = models.CharField(max_length=220, unique=True, editable=False)
    groups = models.ManyToManyField('Group', related_name='users')
    data = JSONField(default={'name': 'test'})
    # 'related_name' intentionally left unset in location field below:
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.name

    def save(self, *args):
        self.uid = randomstring(12)
        return super(User, self).save(*args)







