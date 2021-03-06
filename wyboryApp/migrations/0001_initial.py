# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-04-26 16:39
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Gmina',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nazwa', models.CharField(max_length=64)),
            ],
        ),
        migrations.CreateModel(
            name='Kandydat',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('imie', models.CharField(max_length=42)),
                ('nazwisko', models.CharField(max_length=42)),
            ],
        ),
        migrations.CreateModel(
            name='Obwod',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uprawnieni', models.IntegerField()),
                ('wydane', models.IntegerField()),
                ('niewazne', models.IntegerField()),
                ('gmina', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='wyboryApp.Gmina')),
            ],
        ),
        migrations.CreateModel(
            name='Okreg',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numer', models.IntegerField(unique=True)),
                ('gminy', models.ManyToManyField(through='wyboryApp.Obwod', to='wyboryApp.Gmina')),
            ],
        ),
        migrations.CreateModel(
            name='Wynik',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('glosy', models.IntegerField()),
                ('kandydat', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='wyboryApp.Kandydat')),
                ('obwod', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='wyboryApp.Obwod')),
            ],
        ),
        migrations.AddField(
            model_name='obwod',
            name='okreg',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='wyboryApp.Okreg'),
        ),
        migrations.AlterUniqueTogether(
            name='kandydat',
            unique_together=set([('imie', 'nazwisko')]),
        ),
        migrations.AddField(
            model_name='gmina',
            name='okregi',
            field=models.ManyToManyField(through='wyboryApp.Obwod', to='wyboryApp.Okreg'),
        ),
    ]
