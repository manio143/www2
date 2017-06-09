from django.contrib import admin
from django import forms
from .models import *
from .logic import integrity_check_for_forms
# Register your models here.

class WynikAdminForm(forms.ModelForm):
    class Meta:
        model = Wynik
        fields = ["kandydat", "glosy"]

    def clean(self):
        cleaned_data = self.cleaned_data
        print(cleaned_data)
        wynik = cleaned_data.get("id")
        glosy = cleaned_data.get("glosy")
        if integrity_check_for_forms(wynik, glosy):
            raise forms.ValidationError("Suma głosów nie może przekraczać wydanych kart.")
        return cleaned_data

class WynikInline(admin.TabularInline):
    model = Wynik
    form = WynikAdminForm

class ObwodInline(admin.StackedInline):
    model = Obwod
    can_delete = False
    show_change_link = True

class ObwodAdmin(admin.ModelAdmin):
    inlines = [WynikInline, ]
    
class WithObwodListAdmin(admin.ModelAdmin):
    inlines = [ObwodInline, ]

admin.site.register(Kandydat)

admin.site.register([Okreg, Gmina], WithObwodListAdmin)

admin.site.register(Obwod, ObwodAdmin)
