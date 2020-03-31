from django.contrib import admin

from django.apps import apps
myapp = apps.get_app_config('dapp1')

for key, value in myapp.models.items():
    admin.site.register(value)