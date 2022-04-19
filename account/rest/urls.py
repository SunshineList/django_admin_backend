from django.urls import path, include
from rest_framework.routers import DefaultRouter

router = DefaultRouter()


urlpatterns = [
    url(r'^', include(router.urls, namespace='')),
]