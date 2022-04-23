import uuid

import requests
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.core.validators import URLValidator
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, exceptions, views, viewsets
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.response import Response

from common.models import UploadFileName
from common.rest.serializers import UploadFileSerializer, FileSerializer


class UploadFileApiView(views.APIView):
    parser_classes = (MultiPartParser, FormParser)

    # permission_classes = (permissions.IsAuthenticated,)
    @swagger_auto_schema(
        responses={
            '200': openapi.Response('Success', UploadFileSerializer),
        },
        operation_description='文件上传',
        tags=['文件上传'],
    )
    def post(self, request):
        serializer = UploadFileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        files = serializer.validated_data['files']

        file_urls = []

        for f in files:
            uuid_name = ''.join(str(uuid.uuid1()).split('-')) + '.' + f.name.split('.')[-1]
            file_name = default_storage.save(uuid_name, f)

            host = '{scheme}://{host}'.format(scheme=request.scheme, host=request.get_host())
            file_url = default_storage.url(file_name)

            url_validator = URLValidator()
            try:
                url_validator(file_url)
            except ValidationError:
                file_url = '{host}{file_url}'.format(host=host, file_url=file_url)

            # 存一下文件信息
            UploadFileName.objects.create(uuid_name=uuid_name, name=f.name, url=file_url)

            file_urls.append(file_url)

        return Response({'results': file_urls})


class WeatherApiView(APIView):
    permission_classes = (permissions.AllowAny,)

    def _request(self, city_name):
        url = "http://wthrcdn.etouch.cn/weather_mini"
        params = {
            'city': city_name
        }
        try:
            response = requests.get(url, params=params)
        except Exception as e:
            raise exceptions.ValidationError("未获取到天气信息")
        return response.json()

    @swagger_auto_schema(
        responses={
            '200': openapi.Response('Success', FileSerializer),
        },
        operation_description='获取天气',
        tags=['天气'],
    )
    def get(self, request, *args, **kwargs):
        city_name = self.request.query_params.get('city_name')
        if not city_name:
            raise exceptions.ValidationError("请输入城市名称")
        data = self._request(city_name)
        return Response(data)


class FileViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UploadFileName.objects.all()
    serializer_class = FileSerializer
