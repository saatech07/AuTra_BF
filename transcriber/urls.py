from django.urls import path
from . import views

urlpatterns = [
    path('transcribe/', views.transcribe_audio_view, name='transcribe_audio'),
    path('download_audio/<str:base_name>/', views.download_audio, name='download_audio'),
    path('download_text/<str:base_name>/', views.download_text, name='download_text'),
]
