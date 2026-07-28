# chameleon_api/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('menugroup/', views.menu_group),
    path('menu/', views.menu),
    path('location/', views.location),
    path('tag/', views.tag),
    path('tagrelationship/', views.tag_relationship),
    path('settings/', views.settings),
    path('link/', views.link),
    path('linksgroup/', views.links_group),
    path('kmlshape/', views.kml_shape),
]