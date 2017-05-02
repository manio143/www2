from django.test import TestCase
from django.db import IntegrityError

from .models import *
from .logic import *
# Create your tests here.

class LogicTestCase(TestCase):
    def test_get_stats(self):
        gmina = Gmina.objects.create(nazwa="g")
        okreg = Okreg.objects.create(numer=1)
        obw1 = Obwod.objects.create(gmina=gmina, okreg=okreg,
               uprawnieni=10, wydane=10, niewazne=1)
        obw2 = Obwod.objects.create(gmina=gmina, okreg=okreg,
               uprawnieni=2, wydane=2, niewazne=0)
        
        stats = get_stats(Obwod.objects.filter(id__in=[obw1.id, obw2.id]))

        self.assertEqual(stats["uprawnieni"], obw1.uprawnieni + obw2.uprawnieni)
        self.assertEqual(stats["wydane"], obw1.wydane + obw2.wydane)
        self.assertEqual(stats["niewazne"], obw1.niewazne+obw2.niewazne)
        self.assertEqual(stats["wazne"], 0)
        self.assertEqual(stats["frekwencja"], round(1/12*100, 2))

    def test_integrity_check(self):
        gmina = Gmina.objects.create(nazwa="g")
        okreg = Okreg.objects.create(numer=1)
        obw1 = Obwod.objects.create(gmina=gmina, okreg=okreg,
               uprawnieni=10, wydane=10, niewazne=1)
        cand = Kandydat.objects.create(imie="Jan", nazwisko="Nowak")
        wynik = Wynik.objects.create(kandydat=cand, obwod=obw1, glosy=9)

        # test success
        try:
            integrity_check(wynik)
        except IntegrityError:
            self.fail()

        #test failure
        wynik.glosy = 10
        wynik.save()
        with self.assertRaises(IntegrityError):
            integrity_check(wynik)

    def test_get_candidates(self):
        gmina = Gmina.objects.create(nazwa="g")
        okreg = Okreg.objects.create(numer=1)
        obw1 = Obwod.objects.create(gmina=gmina, okreg=okreg,
               uprawnieni=10, wydane=10, niewazne=1)
        obw2 = Obwod.objects.create(gmina=gmina, okreg=okreg,
               uprawnieni=2, wydane=2, niewazne=0)
        cand = Kandydat.objects.create(imie="Jan", nazwisko="Nowak")
        wynik1 = Wynik.objects.create(kandydat=cand, obwod=obw1, glosy=9)
        wynik2 = Wynik.objects.create(kandydat=cand, obwod=obw2, glosy=2)


        stats = get_stats(Obwod.objects.filter(id__in=[obw1.id, obw2.id]))
        candidates = get_candidates(stats)


        self.assertEqual(11, candidates[0]["glosy"])
        self.assertEqual(cand.__str__(), candidates[0]["nazwa"].__str__())
        self.assertEqual(cand.id, candidates[0]["id"])
