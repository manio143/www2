from django.test import TestCase
from django.db import IntegrityError
from django.test import LiveServerTestCase
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import User

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time

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


class wait_for_page_load(object):
    def __init__(self, browser):
        self.browser = browser

    def __enter__(self):
        self.old_page = self.browser.find_element_by_tag_name('html')

    def page_has_loaded(self):
        new_page = self.browser.find_element_by_tag_name('html')
        return new_page.id != self.old_page.id

    def wait_for(self, condition_function):
        start_time = time.time()
        while time.time() < start_time + 3:
            if condition_function():
                return True
            else:
                time.sleep(0.1)
        raise Exception(
            'Timeout waiting for {}'.format(condition_function.__name__)
        )

    def __exit__(self, *_):
        self.wait_for(self.page_has_loaded)

class wait_for_page_location_change(wait_for_page_load):
    def __enter__(self):
        self.old_hash = self.browser.execute_script("return window.location.hash")
    def page_has_loaded(self):
        new_hash = self.browser.execute_script("return window.location.hash")
        return new_hash != self.old_hash


class UITests(StaticLiveServerTestCase):
    def setUp(self):
        self.browser = webdriver.Chrome()
        self.browser.implicitly_wait(3)
        self.wait = WebDriverWait(self.browser, 10)
        self.setUpDatabase()

    def tearDown(self):
        self.browser.quit()

    def setUpDatabase(self):
        User.objects.create_superuser(username="admin", password="pwd", email="su@root.com")

        okreg = Okreg.objects.create(numer=1) #Okręg 1 w /woj/dolnośląskie
        
        gminaW = Gmina.objects.create(nazwa="Wrocław")
        gminaL = Gmina.objects.create(nazwa="Lubin")

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
        #time.sleep(20)

    # def test_site_index_shows_proper_results(self):
    #     self.open("")
    #     #img_anchor = self.wait.until(EC.element_to_be_clickable(By.PARTIAL_LINK_TEXT, "/woj/dolnośląskie"))
    #     self.wait.until(EC.text_to_be_present_in_element_value(By.XPATH, "//section[@id='mainResult']/table/tbody/tr/td[position()=2]", "106"))
        
    def test_site_goto_obwod(self):
        self.open("")
        with wait_for_page_location_change(self.browser):
            self.browser.find_element_by_id("map_dolnośląskie").click()
        with wait_for_page_location_change(self.browser):        
            self.browser.find_element_by_link_text("Okręg Nr 1").click()
        with wait_for_page_location_change(self.browser):
            self.browser.find_element_by_link_text("Lubin").click()
        