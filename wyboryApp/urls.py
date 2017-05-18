from django.conf.urls import url

from . import views

urls = [
    url(r'^kandydaci', views.KandydatView.as_view()),
    url(r'^$', views.main_page),
    url(r'^login', views.user_login),
    url(r'^logout', views.user_logout),
    url(r'^index', views.index),
    url(r'^woj/(?P<name>.+)', views.woj),
    url(r'^okr/(?P<num>[0-9]+)', views.okr),
    url(r'^gmina/(?P<nazwa>.+?)-(?P<id>[0-9]+)', views.gmina),
    url(r'^edit/(?P<obwod_id>[0-9]+)/(?P<candidate_id>[0-9]+)', views.edit_view),
    url(r'^search', views.search),
]