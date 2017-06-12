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
    search_fields = ["gmina__nazwa", "okreg__numer", "id"]
    list_display = ["__str__", "gmina", "okreg"]
    advanced_search = True

    def get_search_results(self, request, queryset, search_term):
        # queryset, use_distinct = super(ObwodAdmin, self).get_search_results(
        #                                 request, queryset, search_term)
        obwod = request.GET.get("obwod", "")
        gmina = request.GET.get("gmina", "")
        okreg = request.GET.get("okreg", "")
        #TODO: why isn't GET containing stuff?
        #TODO: query like"%param%"
        #TODO: modify self.advanced_search
        print("{}\n{}".format(gmina, okreg))
        return queryset, False
    
class WithObwodListAdmin(admin.ModelAdmin):
    inlines = [ObwodInline, ]

class OkregAdmin(WithObwodListAdmin):
    search_fields = ["gmina__nazwa", "numer", "obwod__id"]
    list_display = ["__str__", "get_gminy"]
    advanced_search = True

    def get_gminy(self, obj):
        return ", ".join([g.__str__() for g in obj.gminy.distinct()])

class GminaAdmin(WithObwodListAdmin):
    search_fields = ["nazwa", "okreg__numer", "obwod__id"]
    list_display = ["__str__", "get_okregi"]
    advanced_search = True
    
    def get_okregi(self, obj):
        return ", ".join([o.__str__() for o in obj.okregi.distinct()])

admin.site.register(Kandydat)

admin.site.register(Okreg, OkregAdmin)
admin.site.register(Gmina, GminaAdmin)

admin.site.register(Obwod, ObwodAdmin)
