from django.db import models

# Create your models here.

class Kandydat(models.Model):
    imie = models.CharField(max_length=42)
    nazwisko = models.CharField(max_length=42)

    def __str__(self):
        return "{} {}".format(self.imie, self.nazwisko)

    class Meta:
        unique_together = ("imie", "nazwisko")

class Okreg(models.Model):
    numer = models.IntegerField(unique=True)
    gminy = models.ManyToManyField("Gmina", through="Obwod")

class Gmina(models.Model):
    nazwa = models.CharField(max_length=64)
    okregi = models.ManyToManyField("Okreg", through="Obwod")

class Obwod(models.Model):
    gmina = models.ForeignKey("Gmina")
    okreg = models.ForeignKey("Okreg")
    uprawnieni = models.IntegerField()
    wydane = models.IntegerField()
    niewazne = models.IntegerField()

class Wynik(models.Model):
    kandydat = models.ForeignKey("Kandydat")
    obwod = models.ForeignKey("Obwod")
    glosy = models.IntegerField()
