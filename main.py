from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import httpx
from models import init_db, record_search, get_stats
from urllib.parse import quote, unquote
from datetime import datetime, timedelta
import pytz
from dateutil import parser

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

async def get_coordinates(city: str):
    url = f"https://nominatim.openstreetmap.org/search?format=json&q={city}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers={"User-Agent": "weather-app"})
        data = response.json()
    if not data:
        return None, None
    return float(data[0]["lat"]), float(data[0]["lon"])

async def get_weather(city: str):
    lat, lon = await get_coordinates(city)
    if lat is None or lon is None:
        return {"error": "Город не найден"}

    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&hourly=temperature_2m&current_weather=true&timezone=auto"
    )
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        data = response.json()

    timezone = data.get("timezone", "UTC")
    tz = pytz.timezone(timezone)
    now = datetime.now(tz)
    end_time = now + timedelta(hours=12)

    hourly_times = data["hourly"]["time"]
    hourly_temps = data["hourly"]["temperature_2m"]

    forecast = [
        {
            "time": (tz.localize(parser.isoparse(time_str)) if parser.isoparse(time_str).tzinfo is None else parser.isoparse(time_str))
                    .strftime("%Y-%m-%d %H:%M"),
            "temperature": temp
        }
        for time_str, temp in zip(hourly_times, hourly_temps)
        if now <= (parser.isoparse(time_str) if parser.isoparse(time_str).tzinfo else tz.localize(parser.isoparse(time_str))) <= end_time
    ]

    weather_desc = {
        0: 'Ясно',
        1: 'В основном ясно',
        2: 'Переменная облачность',
        3: 'Пасмурно',
        45: 'Туман',
        48: 'Инейный туман',
        51: 'Лёгкая морось',
        53: 'Умеренная морось',
        55: 'Сильная морось',
        56: 'Лёгкий ледяной дождь',
        57: 'Сильный ледяной дождь',
        61: 'Лёгкий дождь',
        63: 'Умеренный дождь',
        65: 'Сильный дождь',
        66: 'Лёгкий ледяной дождь',
        67: 'Сильный ледяной дождь',
        71: 'Лёгкий снегопад',
        73: 'Умеренный снегопад',
        75: 'Сильный снегопад',
        77: 'Снежные крупинки',
        80: 'Ливень',
        81: 'Умеренный ливень',
        82: 'Сильный ливень',
        85: 'Слабый снег с дождём',
        86: 'Сильный снег с дождём',
        95: 'Гроза',
        96: 'Гроза с лёгким градом',
        99: 'Гроза с сильным градом'
    }

    current_weather = data.get("current_weather", {})
    if "weathercode" in current_weather:
        current_weather["weather_description"] = weather_desc.get(current_weather["weathercode"], "Неизвестно")

    return {
        "city": city,
        "current_weather": current_weather,
        "forecast": forecast,
        "message": "Данные прогноза на ближайшие 12 часов отсутствуют" if not forecast else ""
    }

@app.get("/", response_class=HTMLResponse)
async def read_form(request: Request):
    last_city = request.cookies.get("last_city")
    if last_city:
        last_city = unquote(last_city)
    return templates.TemplateResponse(request, "form.html", {"last_city": last_city})

@app.post("/weather", response_class=HTMLResponse)
async def get_weather_forecast(request: Request, city: str = Form(...)):
    city = city.strip()
    if not city:
        return templates.TemplateResponse(request, 
            "error.html",
            {"city": city, "message": "Название города не может быть пустым"},
            status_code=400,
        )

    weather_data = await get_weather(city)
    if "error" in weather_data:
        return templates.TemplateResponse(request, 
            "error.html",
            {"city": city, "message": weather_data["error"]}
        )

    await record_search(city)
    response = templates.TemplateResponse(request, 
        "weather.html",
        {"city": city, "weather": weather_data}
    )
    response.set_cookie(key="last_city", value=quote(city), max_age=60 * 60 * 24 * 7)
    return response

@app.get("/stats", response_class=JSONResponse)
async def stats():
    data = await get_stats()
    return [{"city": city, "count": count} for city, count in data]
