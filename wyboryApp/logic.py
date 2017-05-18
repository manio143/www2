from django.db.models import Sum
from django.db import IntegrityError

from .models import *


def get_stats(obwody):
    uprawnieni = obwody.aggregate(Sum("uprawnieni"))["uprawnieni__sum"]
    uprawnieni = uprawnieni if uprawnieni != None else 0
    wydane = obwody.aggregate(Sum("wydane"))["wydane__sum"]
    wydane = wydane if wydane != None else 0
    wazne = 0
    niewazne = obwody.aggregate(Sum("niewazne"))["niewazne__sum"]
    niewazne = niewazne if niewazne != None else 0

    for o in obwody:
        glosy = o.wynik_set.aggregate(Sum("glosy"))["glosy__sum"]
        wazne += glosy if glosy != None else 0

    oddane = wazne + niewazne

    if uprawnieni == 0:
        frekwencja = 0
    else:
        frekwencja = round(oddane / uprawnieni * 100, 2)

    return {
        "uprawnieni": uprawnieni,
        "wydane": wydane,
        "oddane": oddane,
        "wazne": wazne,
        "niewazne": niewazne,
        "frekwencja": frekwencja,
        "obwody": [x.id for x in obwody]
    }


def get_candidates(stats):
    def accumulate(wynik_set, id_list):
        out = 0
        while id_list:
            out+=wynik_set.filter(obwod__id__in=id_list[:200]).aggregate(Sum('glosy'))["glosy__sum"]
            id_list = id_list[200:]
        return out

    kk = list(map(lambda k:
                  {"nazwa": k,
                   "glosy": accumulate(k.wynik_set, stats["obwody"]),
                   "id": k.id},
                  Kandydat.objects.all()))
    for k in kk:
        if stats["oddane"] != 0:
            k["procent"] = round(k["glosy"] / stats["oddane"] * 100, 2)
        else:
            k["procent"] = 0
    return kk


def integrity_check(wynik):
    obwod = Obwod.objects.select_for_update().get(id=wynik.obwod.id)
    wazne = Wynik.objects.filter(
        obwod__id=obwod.id).aggregate(Sum("glosy"))["glosy__sum"]
    if wazne + obwod.niewazne > obwod.wydane:
        raise IntegrityError()
