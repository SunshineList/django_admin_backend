from common.custom_utils.base_request import BaseRequest


class WeatherApi(BaseRequest):

    def get_weather_for_city(self, city_name):
        url = "/weather_mini"

        data = {
            "city": city_name
        }

        response = self.request(url=url, method="get", data=data)

        return response


weather_api = WeatherApi("http://wthrcdn.etouch.cn")
