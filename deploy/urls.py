from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from . import views

app_name = 'deploy'
urlpatterns = [
    path('', views.index, name='index'),
    path('deploy/', csrf_exempt(views.deploy), name='deploy'),
]
