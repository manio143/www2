from django.db import models

# Create your models here.

class Kandydat(models.Model):
    imie = models.CharField(max_length=42)
    nazwisko = models.CharField(max_length=42)

    def __str__(self):
        return "{} {}".format(self.imie, self.nazwisko)

    class Meta:
        unique_together = ("imie", "nazwisko")
        verbose_name_plural = "Kandydaci"

class Okreg(models.Model):
    numer = models.IntegerField(unique=True)
    gminy = models.ManyToManyField("Gmina", through="Obwod")

    def __str__(self):
        return "Okręg nr. {}".format(self.numer)
    
    class Meta:
        verbose_name_plural = "Okręgi"

class Gmina(models.Model):
    nazwa = models.CharField(max_length=64)
    okregi = models.ManyToManyField("Okreg", through="Obwod")

    def __str__(self):
        return "{}".format(self.nazwa)
    
    class Meta:
        verbose_name_plural = "Gminy"

class Obwod(models.Model):
    gmina = models.ForeignKey("Gmina")
    okreg = models.ForeignKey("Okreg")
    uprawnieni = models.IntegerField()
    wydane = models.IntegerField()
    niewazne = models.IntegerField()

    def __str__(self):
        return "Obwód nr. {}".format(self.id)

    class Meta:
        verbose_name_plural = "Obwody"

class Wynik(models.Model):
    kandydat = models.ForeignKey("Kandydat")
    obwod = models.ForeignKey("Obwod")
    glosy = models.IntegerField()
