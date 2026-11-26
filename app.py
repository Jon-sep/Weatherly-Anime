
from flask import Flask, request, render_template_string
import requests

app = Flask(__name__)

# =========================================================
# WEATHER DATA
# =========================================================

def get_weather(city):
    geo = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1, "language": "en", "format": "json"},
        timeout=10
    )
    geo.raise_for_status()

    results = geo.json().get("results")
    if not results:
        return None

    place = results[0]
    lat, lon = place["latitude"], place["longitude"]
    timezone = place.get("timezone", "Asia/Kolkata")

    r = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat,
            "longitude": lon,
            "timezone": timezone,
            "current": "temperature_2m,apparent_temperature,relative_humidity_2m,"
                       "wind_speed_10m,precipitation,rain,weather_code",
            "hourly": "temperature_2m,weather_code",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset",
            "forecast_days": 5
        },
        timeout=10
    )
    r.raise_for_status()
    data = r.json()

    current = data["current"]
    code = current["weather_code"]

    descriptions = {
        0: "Clear Sky", 1: "Mostly Clear", 2: "Partly Cloudy", 3: "Cloudy",
        45: "Fog", 48: "Fog", 51: "Light Drizzle", 53: "Drizzle",
        55: "Heavy Drizzle", 56: "Freezing Drizzle", 57: "Freezing Drizzle",
        61: "Light Rain", 63: "Rain", 65: "Heavy Rain",
        66: "Freezing Rain", 67: "Freezing Rain",
        71: "Light Snow", 73: "Snow", 75: "Heavy Snow", 77: "Snow Grains",
        80: "Rain Showers", 81: "Rain Showers", 82: "Heavy Showers",
        85: "Snow Showers", 86: "Heavy Snow",
        95: "Thunderstorm", 96: "Thunderstorm", 99: "Thunderstorm"
    }

    emojis = {
        0: "☀️", 1: "🌤️", 2: "⛅", 3: "☁️",
        45: "🌫️", 48: "🌫️", 51: "🌦️", 53: "🌦️", 55: "🌧️",
        56: "🌧️", 57: "🌧️", 61: "🌦️", 63: "🌧️", 65: "🌧️",
        66: "🌧️", 67: "🌧️", 71: "🌨️", 73: "❄️", 75: "❄️",
        77: "❄️", 80: "🌦️", 81: "🌧️", 82: "🌧️", 85: "🌨️",
        86: "❄️", 95: "⛈️", 96: "⛈️", 99: "⛈️"
    }

    if code in [45, 48]:
        scene = "fog"
    elif code in [71, 73, 75, 77, 85, 86]:
        scene = "snow"
    elif code in [95, 96, 99]:
        scene = "storm"
    elif code in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82]:
        scene = "rain"
    elif code in [2, 3]:
        scene = "cloudy"
    else:
        scene = "clear"

    hourly = []
    for i in range(8):
        hourly.append({
            "time": data["hourly"]["time"][i][-5:],
            "temp": round(data["hourly"]["temperature_2m"][i]),
            "emoji": emojis.get(data["hourly"]["weather_code"][i], "🌤️")
        })

    daily = []
    for i in range(5):
        daily.append({
            "day": data["daily"]["time"][i],
            "emoji": emojis.get(data["daily"]["weather_code"][i], "🌤️"),
            "weather": descriptions.get(data["daily"]["weather_code"][i], "Weather"),
            "max": round(data["daily"]["temperature_2m_max"][i]),
            "min": round(data["daily"]["temperature_2m_min"][i])
        })

    return {
        "city": place["name"],
        "region": place.get("admin1", ""),
        "country": place.get("country", ""),
        "timezone": timezone,
        "temp": round(current["temperature_2m"]),
        "feels": round(current["apparent_temperature"]),
        "humidity": current["relative_humidity_2m"],
        "wind": current["wind_speed_10m"],
        "precip": current["precipitation"],
        "rain": current["rain"],
        "description": descriptions.get(code, "Weather"),
        "emoji": emojis.get(code, "🌤️"),
        "scene": scene,
        "sunrise": data["daily"]["sunrise"][0][-5:],
        "sunset": data["daily"]["sunset"][0][-5:],
        "hourly": hourly,
        "daily": daily
    }


# =========================================================
# WEBSITE
# =========================================================

PAGE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Weatherly — Anime Sky</title>

<style>
/* ============================================
   WEATHERLY — UNIFIED AESTHETIC GLASS BOXES
   ============================================ */

.stats > div,
.hourly > div,
.daily > div,
.weather-card,
.stat-card,
.hour-card,
.hourly-card,
.daily-card,
.forecast-card {
    background: rgba(255, 255, 255, 0.32) !important;

    backdrop-filter: blur(22px);
    -webkit-backdrop-filter: blur(22px);

    border: 1px solid rgba(255, 255, 255, 0.48) !important;

    border-radius: 22px !important;

    box-shadow:
        0 8px 30px rgba(255, 255, 255, 0.08),
        0 4px 18px rgba(90, 70, 100, 0.08),
        inset 0 1px 0 rgba(255, 255, 255, 0.40);

    transition: all 0.35s ease;
}

/* CLEAR TEXT INSIDE ALL BOXES */
.stats *,
.hourly *,
.daily *,
.weather-card *,
.stat-card *,
.hour-card *,
.hourly-card *,
.daily-card *,
.forecast-card * {
    color: #51445c !important;
    text-shadow: none !important;
}

/* STRONG VALUES */
.stats strong,
.hourly strong,
.daily strong {
    color: #40324f !important;
    font-weight: 800;
}

/* SMALL LABELS */
.stats small,
.hourly small,
.daily small {
    color: #655772 !important;
}

/* SOFT HOVER EFFECT */
.stats > div:hover,
.hourly > div:hover,
.daily > div:hover,
.weather-card:hover,
.forecast-card:hover {
    background: rgba(255, 255, 255, 0.46) !important;

    border-color: rgba(255, 255, 255, 0.75) !important;

    transform: translateY(-4px);

    box-shadow: 0 12px 35px rgba(120, 90, 120, 0.12);
}
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@500;600;700&display=swap');

* { box-sizing:border-box; margin:0; padding:0; }

body {
    font-family:'DM Sans',sans-serif;
    min-height:100vh;
    color:white;
    overflow-x:hidden;
    transition:background 3s, color 2s;
    background:linear-gradient(#83c9ff,#e6d8ff,#ffdfbb);
}

body[data-theme="early"] {
    background:linear-gradient(180deg,#111e49,#506a9b,#c1ccdf);
}
body[data-theme="morning"] {
    background:linear-gradient(180deg,#79caff,#b8e6ff,#ffedc7);
}
body[data-theme="noon"] {
    background:linear-gradient(180deg,#43a9ed,#b9e6ff,#e8ffca);
}
body[data-theme="afternoon"] {
    background:linear-gradient(180deg,#74c4f6,#ffe0b5,#ffcb8a);
}
body[data-theme="dusk"] {
    background:linear-gradient(180deg,#6d83cf,#e7a8cf,#ffd9b0);
}
body[data-theme="sunset"] {
    background:linear-gradient(180deg,#544c99,#ff938d,#ffc86d);
}
body[data-theme="evening"] {
    background:linear-gradient(180deg,#29346c,#696eaa,#e5a5b8);
}
body[data-theme="night"] {
    background:linear-gradient(180deg,#111b46,#293f79,#637eb5);
}
body[data-theme="midnight"] {
    background:linear-gradient(180deg,#06091e,#151d46,#293d66);
}
body[data-theme="sakura"] {
    background:linear-gradient(180deg,#a5cfff,#f6c9de,#fff0df);
}
body[data-theme="ocean"] {
    background:linear-gradient(180deg,#278cb8,#9ce4ed,#d8fff0);
}
body[data-theme="lavender"] {
    background:linear-gradient(180deg,#777ed2,#c1b6f0,#f3d9f6);
}
body[data-theme="peach"] {
    background:linear-gradient(180deg,#ffb6a6,#ffe0bd,#fff3df);
}
body[data-theme="rose"] {
    background:linear-gradient(180deg,#a77ab5,#edb3d1,#ffe4ec);
}
body[data-theme="forest"] {
    background:linear-gradient(180deg,#27685d,#72ad91,#c7e2ae);
}
body[data-theme="galaxy"] {
    background:linear-gradient(180deg,#08051d,#332064,#7452a1);
}
body[data-theme="aurora"] {
    background:linear-gradient(180deg,#031d38,#146a68,#52477c);
}
body[data-theme="snow"] {
    background:linear-gradient(180deg,#99d5f8,#e5f7ff,#ffffff);
}
body[data-theme="japan"] {
    background:linear-gradient(180deg,#9bbce8,#f4d3d8,#fcecd1);
}
body[data-theme="cloud"] {
    background:linear-gradient(180deg,#70b9ff,#e1efff,#ffffff);
}
body[data-theme="summer"] {
    background:linear-gradient(180deg,#39b8e6,#aaf0ca,#f7ffbd);
}
body[data-theme="butterfly"] {
    background:linear-gradient(180deg,#b2b0ef,#e5c8f5,#fff0db);
}
body[data-theme="enchanted"] {
    background:linear-gradient(180deg,#16464b,#3d8275,#b2d49f);
}
body[data-theme="fantasy"] {
    background:linear-gradient(180deg,#443a91,#a481d8,#f4c5ee);
}
body[data-theme="rainy"] {
    background:linear-gradient(180deg,#36476b,#7596ad,#a8c6d4);
}

/* Background world */
.scene {
    position:fixed;
    inset:0;
    overflow:hidden;
    z-index:0;
    pointer-events:none;
}

.sun {
    position:absolute;
    top:12%;
    right:13%;
    width:135px;
    height:135px;
    border-radius:50%;
    background:#fff4bf;
    box-shadow:0 0 60px 25px rgba(255,239,164,.35);
    animation:sunPulse 5s ease-in-out infinite alternate;
    transition:opacity 2s;
}

@keyframes sunPulse {
    to { box-shadow:0 0 100px 45px rgba(255,239,164,.55); }
}

.moon {
    position:absolute;
    top:13%;
    right:14%;
    width:90px;
    height:90px;
    border-radius:50%;
    background:#f5f0ff;
    box-shadow:0 0 50px rgba(255,255,255,.5);
    opacity:0;
    transition:opacity 2s;
}

body[data-theme="night"] .moon,
body[data-theme="midnight"] .moon,
body[data-theme="evening"] .moon,
body[data-theme="galaxy"] .moon,
body[data-theme="aurora"] .moon {opacity:1;}

body[data-theme="night"] .sun,
body[data-theme="midnight"] .sun,
body[data-theme="evening"] .sun,
body[data-theme="galaxy"] .sun,
body[data-theme="aurora"] .sun {opacity:0;}

/* Cloud animations */
.cloud {
    position:absolute;
    width:180px;
    height:50px;
    background:rgba(255,255,255,.45);
    border-radius:50px;
    filter:blur(1px);
}
.cloud:before,.cloud:after {
    content:"";
    position:absolute;
    background:inherit;
    border-radius:50%;
}
.cloud:before {width:75px;height:75px;top:-32px;left:25px;}
.cloud:after {width:100px;height:95px;top:-45px;right:25px;}

.c1 {top:20%;left:-200px;animation:drift 65s linear infinite;}
.c2 {top:37%;left:-200px;opacity:.4;animation:drift 90s linear infinite -25s;transform:scale(.8);}
.c3 {top:10%;left:-200px;opacity:.3;animation:drift 105s linear infinite -40s;transform:scale(1.3);}

@keyframes drift {
    from {left:-250px;}
    to {left:120%;}
}

/* Mountains and rolling hills */
.mountain {
    position:absolute;
    bottom:20%;
    width:100%;
    height:35%;
    background:rgba(82,104,152,.35);
    clip-path:polygon(0 100%,0 65%,12% 20%,25% 70%,38% 8%,51% 67%,65% 18%,78% 70%,89% 25%,100% 75%,100% 100%);
    animation:mountainShift 25s ease-in-out infinite alternate;
}
@keyframes mountainShift {
    to {transform:translateX(2%);}
}

.hill {
    position:absolute;
    width:110%;
    left:-5%;
    height:33%;
    bottom:-5%;
    border-radius:50% 50% 0 0;
    background:rgba(70,142,112,.55);
    animation:hillSway 15s ease-in-out infinite alternate;
}
.hill2 {bottom:-13%;background:rgba(32,105,78,.55);}
@keyframes hillSway {
    to {transform:translateX(2%);}
}

.tree {
    position:absolute;
    bottom:2%;
    left:4%;
    width:100px;
    height:220px;
    transform-origin:bottom;
    animation:treeSway 4s ease-in-out infinite alternate;
}
.tree.right {left:auto;right:5%;animation-delay:-2s;transform:scale(1.2);}
.tree:before {
    content:"";
    position:absolute;
    bottom:0;
    left:44px;
    width:13px;
    height:120px;
    background:#58433b;
}
.tree:after {
    content:"";
    position:absolute;
    bottom:70px;
    width:100px;
    height:150px;
    background:#306c58;
    clip-path:polygon(50% 0,100% 55%,75% 55%,95% 100%,5% 100%,25% 55%,0 55%);
}
@keyframes treeSway {
    from {rotate:-2deg;}
    to {rotate:2deg;}
}

/* Galaxy */
.stars {
    position:absolute;
    inset:0;
    opacity:0;
    transition:opacity 2s;
}
body[data-theme="night"] .stars,
body[data-theme="midnight"] .stars,
body[data-theme="evening"] .stars,
body[data-theme="galaxy"] .stars,
body[data-theme="aurora"] .stars {opacity:1;}

.star {
    position:absolute;
    width:3px;
    height:3px;
    background:white;
    border-radius:50%;
    animation:twinkle 3s ease-in-out infinite alternate;
}
@keyframes twinkle {
    to {opacity:.25;transform:scale(.5);}
}

.aurora {
    position:absolute;
    width:150%;
    height:50%;
    top:0;
    left:-25%;
    background:linear-gradient(90deg,transparent,rgba(65,255,200,.2),rgba(163,120,255,.25),transparent);
    filter:blur(35px);
    opacity:0;
    animation:auroraMove 12s ease-in-out infinite alternate;
}
body[data-theme="aurora"] .aurora {opacity:1;}
@keyframes auroraMove {
    to {transform:translateX(8%) rotate(5deg);}
}

/* Animated particles */
.petal {
    position:fixed;
    top:-25px;
    width:12px;
    height:17px;
    border-radius:80% 20% 80% 20%;
    background:#ffd0e6;
    animation:petalFall linear infinite;
}
@keyframes petalFall {
    to {transform:translateY(110vh) rotate(720deg);}
}
.firefly {
    position:fixed;
    width:5px;
    height:5px;
    border-radius:50%;
    background:#fff9a8;
    box-shadow:0 0 15px #fff9a8;
    animation:fly 7s ease-in-out infinite alternate;
}
@keyframes fly {
    to {transform:translate(100px,-80px);opacity:.1;}
}

#weatherCanvas {
    position:fixed;
    inset:0;
    width:100%;
    height:100%;
    pointer-events:none;
    z-index:1;
}
.fog {
    position:fixed;
    inset:0;
    background:rgba(220,230,240,.25);
    backdrop-filter:blur(3px);
    opacity:0;
    pointer-events:none;
    z-index:1;
}
body[data-weather="fog"] .fog {opacity:1;}
body[data-weather="storm"] {animation:flash 8s infinite;}
@keyframes flash {
    0%,94%,100% {filter:brightness(1);}
    95% {filter:brightness(1.8);}
    96% {filter:brightness(.85);}
    98% {filter:brightness(1.5);}
}

/* Main content */
.app {
    position:relative;
    z-index:3;
    padding:30px 5%;
}
.content {max-width:1200px;margin:auto;}

.nav {
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:15px;
    flex-wrap:wrap;
}
.logo {font-size:27px;font-weight:700;letter-spacing:-1px;}
.logo span {color:#fff0bc;}
.nav-right {display:flex;gap:10px;align-items:center;flex-wrap:wrap;}
.clock,.select {
    background:rgba(255,255,255,.16);
    border:1px solid rgba(255,255,255,.25);
    backdrop-filter:blur(20px);
    border-radius:30px;
    padding:12px 16px;
    color:white;
}
.select {cursor:pointer;max-width:100%;}
.select option {background:#34345e;color:white;}

.search {
    max-width:600px;
    margin:35px auto 25px;
    display:flex;
    gap:5px;
    padding:6px;
    border:1px solid rgba(255,255,255,.3);
    border-radius:50px;
    background:rgba(255,255,255,.16);
    backdrop-filter:blur(20px);
}
.search input {
    flex:1;
    min-width:0;
    padding:15px 20px;
    background:transparent;
    border:0;
    outline:0;
    color:white;
    font-size:16px;
}
.search input::placeholder {color:rgba(255,255,255,.8);}
.search button {
    border:0;
    border-radius:50px;
    padding:12px 22px;
    font-weight:700;
    color:#524d92;
    background:white;
    cursor:pointer;
    transition:.3s;
}
.search button:hover {transform:scale(1.05);}

.hero {
    display:grid;
    grid-template-columns:1.3fr .7fr;
    gap:22px;
    align-items:stretch;
}
.card {
    padding:35px;
    border-radius:32px;
    background:rgba(255,255,255,.16);
    border:1px solid rgba(255,255,255,.25);
    backdrop-filter:blur(22px);
    box-shadow:0 20px 60px rgba(40,40,90,.12);
    animation:appear 1s ease;
}
@keyframes appear {
    from {opacity:0;transform:translateY(25px);}
    to {opacity:1;transform:translateY(0);}
}
.location {font-size:14px;letter-spacing:1.5px;text-transform:uppercase;}
.weather-top {
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:15px;
}
.temp {
    font-size:clamp(75px,10vw,120px);
    font-weight:500;
    letter-spacing:-7px;
    margin:15px 0 0;
}
.desc {font-size:24px;}
.emoji {
    font-size:80px;
    animation:float 4s ease-in-out infinite;
}
@keyframes float {
    50% {transform:translateY(-12px);}
}
.sub {margin-top:12px;opacity:.9;}
.feels {margin-top:18px;}
.story {
    display:flex;
    flex-direction:column;
    justify-content:center;
    line-height:1.8;
}
.story h2 {
    font-family:'Playfair Display',serif;
    font-size:27px;
    margin-bottom:12px;
}
.story p {opacity:.92;}
.story .sun-info {margin-top:18px;}

.stats {
    display:grid;
    grid-template-columns:repeat(4,1fr);
    gap:14px;
    margin-top:23px;
}
.stat {
    padding:22px;
    border-radius:22px;
    background:rgba(255,255,255,.15);
    border:1px solid rgba(255,255,255,.2);
    backdrop-filter:blur(15px);
    transition:.3s;
}
.stat:hover {transform:translateY(-6px);}
.stat-icon {font-size:24px;}
.stat-label {font-size:13px;opacity:.8;margin-top:10px;}
.stat-value {font-size:22px;font-weight:700;margin-top:8px;}

.section {margin-top:35px;}
.heading {
    font-family:'Playfair Display',serif;
    font-size:29px;
    margin-bottom:17px;
}
.hourly {
    display:grid;
    grid-template-columns:repeat(8,1fr);
    gap:10px;
}
.hour,.day {
    text-align:center;
    padding:18px 8px;
    border-radius:21px;
    background:rgba(255,255,255,.15);
    border:1px solid rgba(255,255,255,.2);
    backdrop-filter:blur(15px);
    transition:.3s;
}
.hour:hover,.day:hover {transform:translateY(-5px);}
.hour-time {font-size:13px;opacity:.85;}
.hour-icon {font-size:27px;margin:13px 0;}
.hour-temp {font-size:19px;font-weight:700;}
.daily {display:grid;grid-template-columns:repeat(5,1fr);gap:12px;}
.day-icon {font-size:30px;margin:13px 0;}
.day-weather {font-size:12px;margin-bottom:12px;}
.day-temp {font-size:17px;font-weight:700;}
.footer {text-align:center;margin-top:45px;padding:25px;opacity:.75;font-size:13px;}

@media(max-width:850px) {
    .hero {grid-template-columns:1fr;}
    .stats {grid-template-columns:repeat(2,1fr);}
    .hourly {grid-template-columns:repeat(4,1fr);}
}
@media(max-width:550px) {
    .app {padding:20px 5%;}
    .nav-right {width:100%;}
    .clock {flex:1;text-align:center;}
    .card {padding:24px;}
    .temp {letter-spacing:-4px;}
    .emoji {font-size:60px;}
    .hourly {grid-template-columns:repeat(4,1fr);}
    .daily {grid-template-columns:repeat(2,1fr);}
    .heading {font-size:25px;}
}
</style>
</head>

<body data-theme="morning" data-weather="clear">

<!-- ANIMATED BACKGROUND -->
<div class="scene">
    <div class="sun"></div>
    <div class="moon"></div>
    <div class="aurora"></div>
    <div class="stars" id="stars"></div>
    <div class="cloud c1"></div>
    <div class="cloud c2"></div>
    <div class="cloud c3"></div>
    <div class="mountain"></div>
    <div class="hill"></div>
    <div class="hill hill2"></div>
    <div class="tree"></div>
    <div class="tree right"></div>
</div>

<canvas id="weatherCanvas"></canvas>
<div class="fog"></div>

<div class="app">
<div class="content">

<div class="nav">
    <div class="logo">☁ Weatherly<span>.</span></div>
    <div class="nav-right">
        <div class="clock" id="clock">Loading...</div>
        <select class="select" id="theme">
            <option value="auto">✨ Auto Anime Sky</option>
            <optgroup label="Anime Worlds">
                <option value="sakura">🌸 Sakura Dream</option>
                <option value="ocean">🌊 Ocean Breeze</option>
                <option value="forest">🌿 Green Countryside</option>
                <option value="japan">🏯 Japanese Village</option>
                <option value="cloud">☁ Cloud Kingdom</option>
                <option value="summer">🌻 Summer Fields</option>
                <option value="butterfly">🦋 Butterfly Garden</option>
                <option value="enchanted">🌲 Enchanted Forest</option>
                <option value="fantasy">💜 Fantasy World</option>
            </optgroup>
            <optgroup label="Dream Aesthetics">
                <option value="lavender">🪻 Lavender Dreams</option>
                <option value="peach">🍑 Peach World</option>
                <option value="rose">🌷 Rose World</option>
                <option value="galaxy">🌌 Dream Galaxy</option>
                <option value="aurora">✨ Aurora World</option>
                <option value="snow">❄ Frozen Wonderland</option>
                <option value="rainy">🌧 Rainy Window</option>
            </optgroup>
            <optgroup label="Time Themes">
                <option value="early">🌌 Early Morning</option>
                <option value="morning">🌅 Morning</option>
                <option value="noon">☀ Noon</option>
                <option value="afternoon">🌤 Afternoon</option>
                <option value="dusk">🌆 Dusk</option>
                <option value="sunset">🌇 Sunset</option>
                <option value="evening">🌃 Evening</option>
                <option value="night">🌙 Night</option>
                <option value="midnight">🌠 Midnight</option>
            </optgroup>
        </select>
    </div>
</div>

<form class="search" method="POST">
    <input name="city" value="{{ city }}" placeholder="Search any city..." required>
    <button>Explore ✨</button>
</form>

{% if error %}
<div class="card">
    <h2>🌧️ Oh no!</h2>
    <p style="margin-top:12px">{{ error }}</p>
</div>
{% elif weather %}

<div class="hero">

    <div class="card">
        <div class="location">
            📍 {{ weather.city }}{% if weather.region %}, {{ weather.region }}{% endif %}, {{ weather.country }}
        </div>

        <div class="weather-top">
            <div>
                <div class="temp">{{ weather.temp }}°</div>
                <div class="desc">{{ weather.description }}</div>
                <div class="sub">A little weather magic for your day ✨</div>
            </div>
            <div class="emoji">{{ weather.emoji }}</div>
        </div>

        <div class="feels">Feels like {{ weather.feels }}°</div>
    </div>

    <div class="card story">
        <h2 id="greeting">Welcome to your sky ✨</h2>
        <p id="message">Every sky has its own story.</p>
        <div class="sun-info">🌅 Sunrise: {{ weather.sunrise }}</div>
        <div>🌇 Sunset: {{ weather.sunset }}</div>
        <div style="margin-top:15px;font-size:13px">🌍 Local time: {{ weather.city }}</div>
    </div>

</div>

<div class="stats">
    <div class="stat">
        <div class="stat-icon">💧</div>
        <div class="stat-label">Humidity</div>
        <div class="stat-value">{{ weather.humidity }}%</div>
    </div>
    <div class="stat">
        <div class="stat-icon">🌬️</div>
        <div class="stat-label">Wind</div>
        <div class="stat-value">{{ weather.wind }} km/h</div>
    </div>
    <div class="stat">
        <div class="stat-icon">🌧️</div>
        <div class="stat-label">Precipitation</div>
        <div class="stat-value">{{ weather.precip }} mm</div>
    </div>
    <div class="stat">
        <div class="stat-icon">☔</div>
        <div class="stat-label">Rain</div>
        <div class="stat-value">{{ weather.rain }} mm</div>
    </div>
</div>

<div class="section">
    <h2 class="heading">☁ The Sky Through the Hours</h2>
    <div class="hourly">
        {% for h in weather.hourly %}
        <div class="hour">
            <div class="hour-time">{{ h.time }}</div>
            <div class="hour-icon">{{ h.emoji }}</div>
            <div class="hour-temp">{{ h.temp }}°</div>
        </div>
        {% endfor %}
    </div>
</div>

<div class="section">
    <h2 class="heading">🌸 A Week of Little Adventures</h2>
    <div class="daily">
        {% for d in weather.daily %}
        <div class="day">
            <div>{{ d.day }}</div>
            <div class="day-icon">{{ d.emoji }}</div>
            <div class="day-weather">{{ d.weather }}</div>
            <div class="day-temp">{{ d.max }}° / {{ d.min }}°</div>
        </div>
        {% endfor %}
    </div>
</div>

{% endif %}

<div class="footer">
    Weatherly · Your own little anime sky 🌸
    <br><br>Real weather powered by Open-Meteo
</div>

</div>
</div>

<script>
// =========================================================
// AUTOMATIC CITY LOCAL TIME THEMES
// =========================================================

const timezone = {{ (weather.timezone if weather else "Asia/Kolkata") | tojson }};
const themeBox = document.getElementById("theme");
let manualTheme = false;

function cityTime() {
    return new Date(new Date().toLocaleString("en-US", {timeZone: timezone}));
}

function timeTheme(h) {
    if(h >= 0 && h < 4) return "midnight";
    if(h >= 4 && h < 6) return "early";
    if(h >= 6 && h < 10) return "morning";
    if(h >= 10 && h < 12) return "noon";
    if(h >= 12 && h < 16) return "afternoon";
    if(h >= 16 && h < 18) return "dusk";
    if(h >= 18 && h < 19) return "sunset";
    if(h >= 19 && h < 21) return "evening";
    return "night";
}

function greetingFor(h) {
    if(h >= 0 && h < 4)
        return ["The world is dreaming... 🌌","Let the stars keep you company."];
    if(h >= 4 && h < 6)
        return ["A quiet new beginning 🌙","The world is slowly waking up."];
    if(h >= 6 && h < 10)
        return ["Good morning, sunshine! 🌸","A fresh day. A new little adventure."];
    if(h >= 10 && h < 12)
        return ["A bright morning ☀️","Let the sunshine find you."];
    if(h >= 12 && h < 16)
        return ["Under the summer sky 🌻","Clouds are painting the sky today."];
    if(h >= 16 && h < 18)
        return ["Golden hour magic 🌷","The sky is changing its colours."];
    if(h >= 18 && h < 19)
        return ["A sunset full of dreams 🌇","Take a moment to watch the sunset."];
    if(h >= 19 && h < 21)
        return ["The city lights are waking 🌃","Every little light has a story."];
    return ["Good night, dreamer 🌙","The moon is watching over your world."];
}

function updateClock() {
    const now = cityTime();
    const h = now.getHours();
    const m = String(now.getMinutes()).padStart(2,"0");
    const s = String(now.getSeconds()).padStart(2,"0");
    const ap = h >= 12 ? "PM" : "AM";
    const hr = h % 12 || 12;

    document.getElementById("clock").textContent =
        `${hr}:${m}:${s} ${ap}`;

    if(!manualTheme) {
        document.body.dataset.theme = timeTheme(h);
        themeBox.value = "auto";
    }

    const g = greetingFor(h);
    const greeting = document.getElementById("greeting");
    const message = document.getElementById("message");

    if(greeting && message) {
        greeting.textContent = g[0];
        message.textContent = g[1];
    }
}

themeBox.addEventListener("change", () => {
    if(themeBox.value === "auto") {
        manualTheme = false;
        updateClock();
    } else {
        manualTheme = true;
        document.body.dataset.theme = themeBox.value;
    }
});

updateClock();
setInterval(updateClock,1000);


// =========================================================
// STARS
// =========================================================

const stars = document.getElementById("stars");

for(let i=0;i<110;i++) {
    const star=document.createElement("div");
    star.className="star";
    star.style.left=Math.random()*100+"%";
    star.style.top=Math.random()*80+"%";
    star.style.animationDelay=Math.random()*5+"s";
    stars.appendChild(star);
}


// =========================================================
// SAKURA PETALS
// =========================================================

for(let i=0;i<35;i++) {
    const p=document.createElement("div");
    p.className="petal";
    p.style.left=Math.random()*100+"%";
    p.style.animationDuration=(8+Math.random()*12)+"s";
    p.style.animationDelay=(-Math.random()*15)+"s";
    p.style.opacity=(.2+Math.random()*.7);
    document.body.appendChild(p);
}


// =========================================================
// FIREFLIES
// =========================================================

for(let i=0;i<25;i++) {
    const f=document.createElement("div");
    f.className="firefly";
    f.style.left=Math.random()*100+"%";
    f.style.top=Math.random()*100+"%";
    f.style.animationDelay=Math.random()*8+"s";
    f.style.animationDuration=(5+Math.random()*8)+"s";
    document.body.appendChild(f);
}


// =========================================================
// WEATHER PARTICLES
// =========================================================

const canvas=document.getElementById("weatherCanvas");
const ctx=canvas.getContext("2d");

function resizeCanvas() {
    canvas.width=window.innerWidth;
    canvas.height=window.innerHeight;
}
resizeCanvas();
window.addEventListener("resize",resizeCanvas);

const weatherType={{ (weather.scene if weather else "clear") | tojson }};
document.body.dataset.weather=weatherType;

let particles=[];
let number=weatherType==="storm"?250:
           weatherType==="rain"?150:
           weatherType==="snow"?120:0;

for(let i=0;i<number;i++) {
    particles.push({
        x:Math.random()*canvas.width,
        y:Math.random()*canvas.height,
        speed:weatherType==="snow"?Math.random()*1.5+.5:Math.random()*10+8,
        size:Math.random()*3+1,
        drift:Math.random()*2-1
    });
}

function drawWeather() {
    ctx.clearRect(0,0,canvas.width,canvas.height);

    particles.forEach(p=>{
        if(weatherType==="snow") {
            ctx.fillStyle="rgba(255,255,255,.85)";
            ctx.beginPath();
            ctx.arc(p.x,p.y,p.size,0,Math.PI*2);
            ctx.fill();
            p.y+=p.speed;
            p.x+=p.drift;
        } else {
            ctx.strokeStyle=weatherType==="storm"
                ?"rgba(190,205,255,.5)"
                :"rgba(255,255,255,.5)";
            ctx.beginPath();
            ctx.moveTo(p.x,p.y);
            ctx.lineTo(p.x-4,p.y+15);
            ctx.stroke();
            p.y+=p.speed;
            p.x-=2;
        }

        if(p.y>canvas.height) {
            p.y=-20;
            p.x=Math.random()*canvas.width;
        }
        if(p.x<0) p.x=canvas.width;
    });

    requestAnimationFrame(drawWeather);
}
drawWeather();
/* SCROLL DISAPPEAR EFFECT */

window.addEventListener("scroll", function() {
    if (window.scrollY > 100) {
        document.body.classList.add("scrolling-away");
    } else {
        document.body.classList.remove("scrolling-away");
    }
});
</script>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def home():
    city = "Chennai"
    weather = None
    error = None

    if request.method == "POST":
        city = request.form.get("city", "Chennai").strip() or "Chennai"

    try:
        weather = get_weather(city)
        if weather is None:
            error = "City not found. Please try another city."
    except requests.exceptions.RequestException:
        error = "Weather service is unavailable. Please try again."
    except Exception as e:
        print("Application error:", e)
        error = "Something went wrong while loading the weather."

    return render_template_string(
        PAGE,
        city=city,
        weather=weather,
        error=error
    )


if __name__ == "__main__":
    app.run(debug=True)
