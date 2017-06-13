from django.contrib import admin
from django import forms

from django.contrib.admin.utils import prepare_lookup_value
from django.utils.translation import gettext_lazy
from django.core.exceptions import  ValidationError
from django.contrib.admin.options import IncorrectLookupParameters

from .models import *
from .logic import integrity_check_for_forms

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

class AdvancedSearchForm(forms.Form):
    gmina = forms.CharField()
    okreg = forms.CharField()
    obwod = forms.CharField()

def get_custom_filter(params):
    class AdvancedSearchFilter(admin.filters.ListFilter):
        def expected_parameters(self):
            return params

        used_parameters = {}

        def __init__(self, request, params, model, model_admin):
            self.title = "Advanced Search"
            super().__init__(request, params, model, model_admin)
            print(params)
            for p in self.expected_parameters():
                if p in params:
                    value = params.pop(p)
                    if value != None and value != '':
                        self.used_parameters[p] = prepare_lookup_value(p, value)
            print(params)

        def has_output(self):
            return True

        def queryset(self, request, queryset):
            try:
                def construct_search(field_name):
                    if field_name == "okreg":
                        field_name = "okreg__numer"
                    elif field_name == "gmina":
                        field_name = "gmina__nazwa"
                    elif field_name == "obwod":
                        field_name = "obwod__id"

                    return "%s__icontains" % field_name

                query_params = {
                    construct_search(field): value
                    for field, value in self.used_parameters.items()
                }

                ret = queryset.filter(**query_params).distinct()
                print(ret)
                return ret
            except (ValueError, ValidationError) as e:
                # Fields may raise a ValueError or ValidationError when converting
                # the parameters to the correct type.
                raise IncorrectLookupParameters(e)

        def choices(self, changelist):
            yield {
                'selected': bool(self.used_parameters),
                'query_string': changelist.get_query_string({}, self.expected_parameters()),
                'display': gettext_lazy('All'),
            }
            for key, value in self.used_parameters.items():
                yield {
                    'selected': bool(value),
                    'query_string': changelist.get_query_string({key: value}, []),
                    'display': "{}: {}".format(key, value),
                }
    return AdvancedSearchFilter

class MyModelAdminBase(admin.ModelAdmin):
    advanced_search = {}

    def lookup_allowed(self, lookup, _):
        if lookup in self.advanced_search.values():
            return True
        return super(MyModelAdminBase, self).lookup_allowed(lookup, _)

    def get_search_results(self, request, queryset, search_term):
        obwod = request.GET.get("obwod", request.GET.get("id", ""))
        gmina = request.GET.get("gmina", request.GET.get("nazwa", "")) 
        okreg = request.GET.get("okreg", request.GET.get("numer", ""))
        self.advanced_search["obwod_value"] = obwod
        self.advanced_search["gmina_value"] = gmina
        self.advanced_search["okreg_value"] = okreg
        return super(MyModelAdminBase, self).get_search_results(
                                               request, queryset, search_term)

class ObwodAdmin(MyModelAdminBase):
    inlines = [WynikInline, ]
    search_fields = ["gmina__nazwa", "okreg__numer", "id"]
    list_display = ["__str__", "gmina", "okreg"]
    list_filter = [get_custom_filter(["id", "gmina", "okreg"])]
    advanced_search = {"obwod": "id", "gmina":"gmina", "okreg":"okreg"}

class OkregAdmin(MyModelAdminBase):
    inlines = [ObwodInline, ]
    search_fields = ["gmina__nazwa", "numer", "obwod__id"]
    list_display = ["__str__", "get_gminy"]
    list_filter = [get_custom_filter(["numer", "gmina", "obwod"])]
    advanced_search = {"obwod": "obwod", "gmina":"gmina", "okreg":"numer"}

    def get_gminy(self, obj):
        return ", ".join([g.__str__() for g in obj.gminy.distinct()])

class GminaAdmin(MyModelAdminBase):
    inlines = [ObwodInline, ]
    search_fields = ["nazwa", "okreg__numer", "obwod__id"]
    list_display = ["__str__", "get_okregi"]
    list_filter = [get_custom_filter(["nazwa", "obwod", "okreg"])]
    advanced_search = {"obwod": "obwod", "gmina":"nazwa", "okreg":"okreg"}
    
    def get_okregi(self, obj):
        return ", ".join([o.__str__() for o in obj.okregi.distinct()])

admin.site.register(Kandydat)

admin.site.register(Okreg, OkregAdmin)
admin.site.register(Gmina, GminaAdmin)

admin.site.register(Obwod, ObwodAdmin)
