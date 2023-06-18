import logging
from urllib.parse import urljoin

import requests
from rest_framework import exceptions


class BaseRequest(object):
    def __init__(self, host):
        self.host = host

    def _url(self, url) -> str:
        return urljoin(self.host, url)

    def request(self, url, data, *, method="post", **kwargs):
        """
        通用request类 这里处理请求
        """
        
        method = str(method).lower()

        data_map = {"method": method, "url": self._url(url), "timeout": 5}

        if method == "get":
            data_map.update({"params": data})
        else:
            data_map.update({"data": data})

        try:
            response = requests.request(**data_map, **kwargs)
        except (requests.ConnectionError, requests.Timeout) as e:
            raise exceptions.ValidationError('网络错误，无法连接系统！')
        except exceptions.ValidationError as e:
            raise exceptions.ValidationError(e)
        except Exception as e:
            logging.error(e)
            raise exceptions.ValidationError('未知错误，请联系管理员！')

        response = response.json()

        return response
