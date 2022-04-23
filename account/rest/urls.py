from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from account.rest.api import CaptchaView, LoginApiView, UserInfoView, AccountViewSet

router = DefaultRouter()

router.register("account", AccountViewSet, basename="account")

urlpatterns = [
    re_path(r'^captcha/$', CaptchaView.as_view(), name='captcha'),
    re_path(r'^login/$', LoginApiView.as_view(), name='login'),
    re_path(r'^info/$', UserInfoView.as_view(), name='info'),
]

urlpatterns += router.urls
