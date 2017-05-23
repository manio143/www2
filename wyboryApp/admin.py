from django.contrib import admin
from .models import *
# Register your models here.

myModels = [Kandydat, Okreg, Obwod, Gmina, Wynik]  # iterable list

admin.site.register(myModels)
