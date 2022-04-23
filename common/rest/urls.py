from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter

from common.rest.api import UploadFileApiView, FileViewSet, WeatherApiView

router = DefaultRouter()

router.register('file_list', FileViewSet, basename='file_list')

urlpatterns = [
    path("upload/", UploadFileApiView.as_view()),
    path("weather/", WeatherApiView.as_view(), name="weather"),
]

urlpatterns += router.urls
