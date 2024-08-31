from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views
from .views import download_image


urlpatterns = [
    path('', views.process_video, name='process_video'),
    path('download_image/<str:filename>/', download_image, name='download_image'),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

