import import_declare_test
import sys
import json
import requests
from urllib.parse import urljoin, urlencode

from splunklib.searchcommands import dispatch, GeneratingCommand, Configuration, Option

WEATHER_API_URL = 'https://api.openweathermap.org/data/2.5/'


def build_weather_api_url(path, query, token, units):
    return urljoin(WEATHER_API_URL, path + "?" + urlencode(dict(q=query, appid=token, units=units)))


def get_encrypted_weather_api_token(search_command):
    secrets = search_command.service.storage_passwords
    for secret in secrets:
        if 'openweathermap_apikey' in secret.clear_password:
            dict_secret = json.loads(secret.clear_password)
            api_key = dict_secret['openweathermap_apikey']
    return api_key


@Configuration()
class WeatherSearch(GeneratingCommand):
    location = Option(require=True)

    def generate(self):
        token = get_encrypted_weather_api_token(self)
        if token is None:
            raise ValueError('No OpenWeatherMap API key found. Please add one and try again.')

        # call out to the weather API
        url = build_weather_api_url('forecast', self.location, token, 'metric')

        # make request
        response = requests.get(url, timeout=10)

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as ex:
            return f'Error: {ex}'

        result = response.json()['list'][0]
        lat = response.json()['city']['coord']['lat']
        lon = response.json()['city']['coord']['lon']
        message = {
            'time': result['dt_txt'],
            'temperature_c': result['main']['temp'],
            'temperature_f': round(result['main']['temp'] * 1.8 + 32, 2),
            'lat': lat,
            'lon': lon,
            'wind_degrees': result['wind']['deg'],
            'wind_speed_kph': int(result['wind']['speed']) * 3.6,
            'wind_speed_mph': round(int(result['wind']['speed']) * 2.23694, 2),
            'description': result['weather'][0]['description']
        }
        yield {
            '_raw': message,
            '_time': result['dt'],
            'lat': lat,
            'lon': lon,
            'temperature_c': result['main']['temp'],
            'temperature_f': round(result['main']['temp'] * 1.8 + 32, 2),
            'wind_degrees': result['wind']['deg'],
            'wind_speed_kph': int(result['wind']['speed']) * 3.6,
            'wind_speed_mph': round(int(result['wind']['speed']) * 2.23694, 2),
            'description': result['weather'][0]['description'],
        }


dispatch(WeatherSearch, sys.argv, sys.stdin, sys.stdout, __name__)
