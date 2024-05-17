from django.urls import path
from fim.views.auth import fim_logout

urlpatterns = [
    path('fim/logout/', fim_logout, name='fim_logout'),
]
