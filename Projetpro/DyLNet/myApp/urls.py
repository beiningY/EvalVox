# myproject/myApp/urls.py
from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'), 
    path('conversion/', views.conversion_view, name='conversion'), 
    path('DER/', views.DER_view, name='DER'),
    path('WER/', views.WER_view, name='WER'),
    path('DERWER/', views.DERWER_view, name='DERWER'),
    path('download/<str:file_name>', views.download_file, name='download_file'),
    path('derwer-data/', views.DERWER_view, name='derwer_data'),
]
