from django.test import TestCase
from django.db import IntegrityError
from django.test import LiveServerTestCase
from django.contrib.auth.models import User

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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

    def test_no_votes_get_candidates(self):
        """
        Make sure get_candidates doesn't throw if a candidate has no Wynik objects
        """
        gmina = Gmina.objects.create(nazwa="g")
        okreg = Okreg.objects.create(numer=1)
        obw1 = Obwod.objects.create(gmina=gmina, okreg=okreg,
               uprawnieni=10, wydane=10, niewazne=1)
        cand = Kandydat.objects.create(imie="Jan", nazwisko="Nowak")


        stats = get_stats(Obwod.objects.filter(id=obw1.id))
        candidates = get_candidates(stats)


        self.assertEqual(0, candidates[0]["glosy"])

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


class UITests(LiveServerTestCase):
    def setUp(self):
        self.browser = webdriver.Chrome()
        self.browser.implicitly_wait(3)
        self.wait = WebDriverWait(self.browser, 10)

    def tearDown(self):
        self.browser.quit()

    def setUpDatabase(self):
        User.objects.create_superuser(username="admin", password="pwd", email="su@root.com")

        okreg = Okreg.objects.create(numer=1) #Okręg 1 w /woj/dolnośląskie
        
        gminaW = Gmina.objects.create(nazwa="Wrocław")
        gminaL = Gmina.object.create(nazwa="Lubin")

        obwod1 = Obwod.objects.create(gmina=gminaW, okreg=okreg,
                                      uprawnieni=1000, wydane=800, niewazne=20)
        obwod2 = Obwod.objects.create(gmina=gminaL, okreg=okreg,
                                      uprawnieni=640, wydane=600, niewazne=3)

        cand1 = Kandydat.objects.create(imie="Jan", nazwisko="Nowak")
        cand2 = Kandydat.objects.create(imie="Piotr", nazwisko="Kowalski")

        Wynik.objects.create(kandydat=cand1, obwod=obwod1, glosy=30)
        Wynik.objects.create(kandydat=cand2, obwod=obwod1, glosy=50)
        Wynik.objects.create(kandydat=cand1, obwod=obwod2, glosy=76)
        Wynik.objects.create(kandydat=cand2, obwod=obwod2, glosy=12)

    def open(self, url):
        self.browser.get("%s%s" % (self.live_server_url, url)) # use the live server url

    def test_site_launches(self):
        self.open("")
        assert 'Wybory Prezydenta Rzeczypospolitej Polskiej 2000' in self.browser.title

    def test_site_index_shows_proper_results(self):
        self.open("")
        #img_anchor = self.wait.until(EC.element_to_be_clickable(By.PARTIAL_LINK_TEXT, "/woj/dolnośląskie"))
        self.wait.until(EC.text_to_be_present_in_element_value(By.XPATH, "//section[@id='mainResult']/table/tbody/tr/td[position()=2]"), "106")
        
        