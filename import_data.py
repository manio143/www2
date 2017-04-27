# http://prezydent2015.pkw.gov.pl/325_Wyniki_Polska
# http://prezydent2000.pkw.gov.pl/wb/wb.html

import os
import csv
from itertools import groupby
from wyboryApp.models import Okreg, Gmina, Kandydat, Wynik, Obwod

data_header = []

def process_reader(reader):
    def inner():
        global data_header
        first = True
        for _row in reader:
            row = list(_row)
            if first:
                first = False
                if not data_header:
                    data_header = row
            else:
                #print(row[4:])
                yield tuple([int(row[0]), row[1], row[2], row[3], int(row[4]), row[5], row[6]]+[int(x) for x in row[7:]])
    return list(inner())

def load_data(dirname):
    files = filter(lambda st: st.endswith(".csv"), os.listdir(dirname))
    data = []
    for filename in files:
        file = open(os.path.join(dirname, filename))
        reader = csv.reader(file)
        data += process_reader(reader)
    return data

def merge_records(records):
    return list(map(sum, zip(*map(lambda x: x[7: ], records))))

def group_by_obwod(data):
    key_func = lambda x: x[4]
    _sorted = sorted(data, key=key_func) #sort by obwod
    grouped = groupby(_sorted, key_func)
    grouped_list = [(obwod, list(rows)) for (obwod, rows) in grouped]
    return [(obwod, merge_records(rows)) for (obwod, rows) in grouped_list]

def group_by_gmina(data):
    key_func = lambda x: x[2]
    _sorted = sorted(data, key=key_func) #sort by gmina
    grouped = groupby(_sorted, key_func)
    grouped_list = [(gmina, list(rows)) for (gmina, rows) in grouped]
    return [(gmina, rows[0][1], merge_records(rows), rows) for (gmina, rows) in grouped_list]

def group_by_okrag(data):
    key_func = lambda x: x[0]
    _sorted = sorted(data, key=key_func) #sort by okręg
    grouped = groupby(_sorted, key_func)
    grouped_list = [(okreg, list(rows)) for (okreg, rows) in grouped]
    return [(okreg, merge_records(rows), rows) for (okreg, rows) in grouped_list]

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

def group_by_wojewodztwo(data):
    def lower_filter(wojewodztwo):
        okregi = WOJEWODZTWO_OKREGI[wojewodztwo]
        _data = list(filter(lambda r: r[0] in okregi, data))
        return (wojewodztwo, merge_records(_data), _data)
    return [lower_filter(woj) for woj in WOJEWODZTWO_OKREGI.keys()]

def candidates(merged_data):
    names = data_header[12: ]
    _votes = merged_data[5: ]
    return [{"nazwa":name, "głosy":votes} for name, votes in zip(names, _votes)]


def generate_all(path):
    data = load_data(path)
    names = data_header[12: ]
    for name in names:
        nameparts = name.split(' ')
        print(nameparts)
        Kandydat.objects.create(imie=nameparts[0], nazwisko=nameparts[-1])

    for wojewodztwo, merged_data, wdata in group_by_wojewodztwo(data):
        okregi = group_by_okrag(wdata)
        for okreg, omerged_data, odata in okregi:
            gminy = group_by_gmina(odata)
            o = Okreg.objects.create(numer=okreg)
            for gmina, num, gmerged_data, gdata in gminy:
                obwody = group_by_obwod(gdata)
                g = Gmina.objects.create(nazwa=gmina)
                for obwod,oomerged in obwody:
                    oo = Obwod.objects.create(gmina=g, okreg=o, uprawnieni=oomerged[0], wydane=oomerged[1], niewazne=oomerged[3])
                    candidates_ = candidates(oomerged)
                    for candidate in candidates_:
                        nameparts = candidate["nazwa"].split(' ')
                        k = Kandydat.objects.filter(imie=nameparts[0]).filter(nazwisko=nameparts[-1])[0]
                        Wynik.objects.create(kandydat=k, glosy=candidate["głosy"], obwod=oo)

#generate_all()
