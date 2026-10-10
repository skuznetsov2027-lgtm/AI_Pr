from pathlib import Path

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.weather import get_weather, WeatherError


BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="Погода в місті",
    description="Поточна погода на основі Open-Meteo API"
)


@app.exception_handler(WeatherError)
async def weather_error_handler(request: Request, exc: WeatherError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )


templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates")
)


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """Показує головну сторінку."""

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )


@app.get("/api/weather")
def api_weather(city: str = Query(..., min_length=1)):
    """Повертає погоду у форматі JSON."""

    return get_weather(city)
