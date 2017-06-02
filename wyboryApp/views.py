from json import loads

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.views import View
from django.db.models import Sum
from django.views.generic import ListView
from django.contrib.auth import authenticate, logout, login
from django import forms
from django.db import transaction, IntegrityError

from django.middleware import csrf

from . import models
from .logic import get_stats, get_candidates, integrity_check

from django.db.models import Model
from django.db.models.query import QuerySet
from django.forms import model_to_dict

def good_to_go(o):
    if hasattr(o, 'to_dict'):
        return o.to_dict()
    elif issubclass(o.__class__, Model):
        if hasattr(o, '__str__'):
            return o.__str__()
        return model_to_dict(o)
    elif issubclass(o.__class__, QuerySet) or isinstance(o, list):
        return [good_to_go(m) for m in o]
    elif isinstance(o, dict):
        return {k: good_to_go(v) for k, v in o.items()}
    else:
        return o

WOJEWODZTWO_OKREGI = {
    "dolnośląskie": (1, 2, 3, 4),
    "kujawsko-pomorskie": (5, 6, 7),
    "lubelskie": (8, 9, 10, 11, 12),
    "lubuskie": (13, 14),
    "łódzkie": (15, 16, 17, 18, 19),
    "małopolskie": (20, 21, 22, 23, 24, 25, 26, 27),
    "mazowieckie": (28, 29, 30, 31, 32, 33, 34, 35, 36),
    "opolskie": (37, 38),
    "podkarpackie": (39, 40, 41, 42),
    "podlaskie": (43, 44, 45),
    "pomorskie": (46, 47, 48),
    "śląskie": (49, 50, 51, 52, 53, 54),
    "świętokrzyskie": (55, 56),
    "warmińsko-mazurskie": (57, 58, 59),
    "wielkopolskie": (60, 61, 62, 63, 64),
    "zachodniopomorskie": (65, 66, 67, 68)
}


class KandydatView(ListView):
    model = models.Kandydat

    template_name = "kandydat.html"


class KandydatForm(forms.Form):
    imie = forms.CharField(label="Imię")
    nazwisko = forms.CharField(label="Nazwisko")

    def clean(self):
        if self.cleaned_data.get("nazwisko") in ("Nowak", "Kowalski"):
            self.add_error("nazwisko", "Nie chcemy tych panów!")


def szukaj_kandydat(request):
    if request.method == "POST":
        form = KandydatForm(request.POST)
        if form.is_valid():
            return HttpResponse("Kandydat: {} {}".format(form.imie, form.nazwisko))
        else:
            return HttpResponse(form.nazwisko.error_messages)


class LoginForm(forms.Form):
    user = forms.CharField(label="Login")
    password = forms.CharField(widget=forms.PasswordInput)


def user_login(request):
    if request.method == "GET":
        return render(request, "login.html", {"form": LoginForm()})
    elif request.method == "POST":
        form = LoginForm(request.POST)
        form.is_valid()
        user = authenticate(username=form.cleaned_data["user"], password=form.cleaned_data["password"])
        if user is None:
            result = JsonResponse({"error": "Invalid login or password."})
            result.status_code = 420
            return result
        else:
            login(request, user)
            return JsonResponse({"auth":True})


def user_logout(request):
    logout(request)
    return JsonResponse({"auth":False})

def context(request, data, more):
    stats = get_stats(data)

    kandydaci = get_candidates(stats)

    stats.pop("obwody", None)
    return {
        "auth": True if request.user.is_authenticated else False,
        "stats": stats,
        "mainResult": kandydaci,
        "more": more,
        "currUrl": request.path,
    }
def view(request, data, template, more=None):
    _context = context(request, data, more)

    return render(request, template, _context)

def json(request, data, type, more=None):
    _context = good_to_go(context(request, data, more))
    _context["type"] = type
    return JsonResponse(_context, safe=False)

def main_page(request):
    return view(request, models.Obwod.objects.filter(id__lt=0), "index.html")

def index(request):
    return json(request, models.Obwod.objects.all(), "main")

def woj(request, name):
    okregi = list(WOJEWODZTWO_OKREGI[name])
    data = models.Obwod.objects.filter(okreg__numer__in=okregi)
    if not list(data):
        return HttpResponseRedirect("/")
    return json(request, data, "details",
                {"links":
                 [{"url": "/okr/{}".format(x), "nazwa": "Okręg Nr {}".format(x)}
                  for x in okregi]
                })


def okr(request, num):
    data = models.Obwod.objects.filter(okreg__numer__in=[num])
    if not list(data):
        return HttpResponseRedirect("/")
    return json(request, data, "details",
                {"links":
                 [{"url": "/gmina/{}-{}".format(x.nazwa, x.id), "nazwa": "{}".format(
                     x.nazwa)} for x in models.Okreg.objects.get(numer=num).gmina_set.distinct()]
                })

def gmina(request, nazwa, id):
    data = models.Obwod.objects.filter(gmina__id=id)
    if not list(data):
        return HttpResponseRedirect("/")
    return json(request, data, "gmina",
                {"results":
                 [{"id": x.id, "result": get_candidates(get_stats(data.filter(
                     id=x.id))), "max": get_stats(data.filter(
                     id=x.id))["wydane"] - get_stats(data.filter(
                     id=x.id))["niewazne"], "miejsce": "w obwodzie nr {}".format(x.id)} for x in data]
                })


class EditForm(forms.Form):
    oddane = forms.IntegerField()
    
    def clean(self):
        if self.cleaned_data.get("oddane") < 0:
            self.add_error("oddane", "Ujemna wartość!")


def edit_view(request, obwod_id, candidate_id):
    candidate = models.Kandydat.objects.get(id=candidate_id)
    wynik = models.Wynik.objects.filter(
        obwod__id=obwod_id).get(kandydat__id=candidate_id)

    success = None
    error = None

    if request.method == "POST":
        form = EditForm(request.POST)
        if form.is_valid():
            oddane = form.cleaned_data["oddane"]
            try:
                with transaction.atomic():
                    wynik.glosy = oddane
                    wynik.save()
                    integrity_check(wynik)
                    success = "Zaktualizowano dane."
            except IntegrityError:
                error = "Liczba głosów oddanych w obwodzie nie może przekraczać liczby wydanych kart."
        else:
            error = "Błąd w przesłanych danych"
    else:
        form = EditForm(initial={"oddane": wynik.glosy})
        csrf.get_token(request)

    context = {
        "nazwa": "{} {}".format(candidate.imie, candidate.nazwisko),
        "obwod": obwod_id,
        "success": success,
        "error": error,
    }
    if "return" in request.GET:
        context["back"] = request.GET["return"]

    return JsonResponse(good_to_go(context))


def search(request):
    if "q" not in request.GET:
        return HttpResponseRedirect("/")

    phrase = request.GET["q"]
    gminy = models.Gmina.objects.filter(nazwa__contains=phrase)

    context = {
        "gminy": [{"nazwa": x.nazwa, "id": x.id} for x in gminy]
    }

    return JsonResponse(good_to_go(context), safe=False)

def json_to_dict(get_response):
    def middleware(request):
        body_unicode = request.body.decode('utf-8')
        if body_unicode.startswith("{"):
            request.POST = loads(body_unicode)
        response = get_response(request)
        return response
    return middleware
