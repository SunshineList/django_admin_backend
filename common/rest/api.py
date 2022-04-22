import uuid

from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.core.validators import URLValidator
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, exceptions, views
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.response import Response

from common.models import UploadFileName
from common.rest.serializers import UploadFileSerializer


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
