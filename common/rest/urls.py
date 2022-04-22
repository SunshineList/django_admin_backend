from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter

from common.rest.api import UploadFileApiView

router = DefaultRouter()

urlpatterns = [path("upload/", UploadFileApiView.as_view())]

urlpatterns += router.urls
