import requests

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
TIMEOUT = 10

class WeatherError(Exception):
    """Помилка, яку можна зрозуміло показати користувачу."""

    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

def get_json(url: str, params: dict) -> dict:
    """Виконує HTTP-запит і перевіряє відповідь сервісу."""

    try:
        response = requests.get(
            url,
            params=params,
            timeout=TIMEOUT
        )
        response.raise_for_status()

    except requests.Timeout:
        raise WeatherError(
            "Зовнішній сервіс не відповів вчасно. Спробуйте ще раз.",
            504
        )

    except requests.ConnectionError:
        raise WeatherError(
            "Не вдалося підключитися до сервісу погоди.",
            503
        )

    except requests.HTTPError:
        raise WeatherError(
            "Зовнішній сервіс повернув HTTP-помилку.",
            502
        )

    except requests.RequestException:
        raise WeatherError(
            "Помилка під час запиту до сервісу погоди.",
            502
        )

    try:
        data = response.json()
    except ValueError:
        raise WeatherError(
            "Сервіс повернув відповідь, яка не є JSON.",
            502
        )

    if not isinstance(data, dict):
        raise WeatherError(
            "Непередбачений формат відповіді сервісу.",
            502
        )

    return data

def get_weather(city: str) -> dict:
    """Повертає назву міста, температуру та швидкість вітру."""

    if not isinstance(city, str) or not city.strip():
        raise WeatherError(
            "Введіть назву міста.",
            422
        )

    city = city.strip()

    geo_data = get_json(
        GEOCODING_URL,
        {
            "name": city,
            "count": 1,
            "language": "uk",
            "format": "json"
        }
    )
    if "results" not in geo_data:
        raise WeatherError(
            f"Місто «{city}» не знайдено.",
            404
        )

    results = geo_data["results"]

    if not isinstance(results, list):
        raise WeatherError(
            "Неправильний формат даних про місто.",
            502
        )

    if not results:
        raise WeatherError(
            f"Місто «{city}» не знайдено.",
            404
        )

    place = results[0]

    if not isinstance(place, dict):
        raise WeatherError(
            "Неправильний формат даних про місто.",
            502
        )

    latitude = place.get("latitude")
    longitude = place.get("longitude")
    city_name = place.get("name")

    if (
        not isinstance(latitude, (int, float))
        or isinstance(latitude, bool)
        or not isinstance(longitude, (int, float))
        or isinstance(longitude, bool)
        or not isinstance(city_name, str)
        or not city_name.strip()
    ):
        raise WeatherError(
            "У відповіді немає коректних координат міста.",
            502
        )
    
    weather_data = get_json(
        FORECAST_URL,
        {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,wind_speed_10m",
            "wind_speed_unit": "kmh"
        }
    )

    current = weather_data.get("current")

    if not isinstance(current, dict):
        raise WeatherError(
            "Сервіс не повернув дані про поточну погоду.",
            502
        )

    temperature = current.get("temperature_2m")
    wind_speed = current.get("wind_speed_10m")

    if (
        not isinstance(temperature, (int, float))
        or isinstance(temperature, bool)
        or not isinstance(wind_speed, (int, float))
        or isinstance(wind_speed, bool)
    ):
        raise WeatherError(
            "Дані про температуру або вітер мають неправильний формат.",
            502
        )

    return {
        "city": city_name,
        "temperature": temperature,
        "wind_speed": wind_speed,
        "temperature_unit": "°C",
        "wind_speed_unit": "км/год"
    }