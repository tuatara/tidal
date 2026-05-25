from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import cache
from icalendar import Event, vDatetime
import requests


def _date_range(start: date, days: int) -> list[date]:
    return [start + timedelta(days=i) for i in range(days)]


def moon_phase(grade: int):
    if grade == 0:
        return "New moon"
    if grade < 0.25:
        return "Waxing crescent moon"
    if grade == 0.25:
        return "First quarter moon"
    if grade < 0.5:
        return "Waxing gibbous moon"
    if grade == 0.5:
        return "Full moon"
    if grade < 0.75:
        return "Waning gibbous moon"
    if grade == 0.75:
        return "Last quarter moon"
    if grade <= 1:
        return "Waning crescent moon"
    return "Moon is likely destroyed"


def _fetch_astro_api(api_key: str, lat, lon, days: int = 30):
    response = requests.get(
        f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{lat},{lon}/next{days}days",
        params={"key": api_key, "include": "days", "elements": "datetime,moonphase,moonrise", "timezone": "UTC"},
    )
    response.raise_for_status()
    return response


def _fetch_tidal_api(api_key: str, lat, lon, days: int = 30):
    response = requests.get(
        "https://api.niwa.co.nz/tides/data",
        headers={"x-apikey": api_key},
        params={"lat": lat, "long": lon, "numberOfDays": days},
    )
    response.raise_for_status()
    return response


def fetch_astro_data(api_key: str, lat, lon, days: int = 30) -> dict:
    today = datetime.now(timezone.utc).date()
    requested = _date_range(today, int(days))

    all_days: dict[date, dict] = {}
    missing = []

    for dt in requested:
        hit = cache.get("astro", lat, lon, dt)
        if hit is not None:
            all_days[dt] = hit
        else:
            missing.append(dt)

    if missing:
        for day in _fetch_astro_api(api_key, lat, lon, days).json()["days"]:
            dt = date.fromisoformat(day["datetime"])
            cache.put("astro", lat, lon, dt, day)
            all_days[dt] = day

    return {"timezone": "UTC", "days": [all_days[dt] for dt in requested if dt in all_days]}


def fetch_tidal_data(api_key: str, lat, lon, days: int = 30) -> dict:
    today = datetime.now(timezone.utc).date()
    requested = _date_range(today, int(days))

    all_days: dict[date, dict] = {}
    missing = []

    for dt in requested:
        hit = cache.get("tides", lat, lon, dt)
        if hit is not None:
            all_days[dt] = hit
        else:
            missing.append(dt)

    if missing:
        fresh: dict[date, list] = {}
        for value in _fetch_tidal_api(api_key, lat, lon, days).json()["values"]:
            dt = datetime.fromisoformat(value["time"]).date()
            fresh.setdefault(dt, []).append(value)
        for dt, values in fresh.items():
            day_data = {"values": values}
            cache.put("tides", lat, lon, dt, day_data)
            all_days[dt] = day_data

    return {"values": [v for dt in requested for v in all_days.get(dt, {}).get("values", [])]}


def update_astro_calendar(cal, payload):
    for day in payload["days"]:
        if not day.get("moonrise", False):
            continue
        event = Event()

        dtstart = datetime.strptime(
            "{} {}".format(day["datetime"], day["moonrise"]), "%Y-%m-%d %H:%M:%S"
        ).astimezone(ZoneInfo(payload["timezone"]))
        event["uid"] = int(dtstart.timestamp())
        event["dtstamp"] = vDatetime(dtstart).to_ical()
        event["dtstart"] = vDatetime(dtstart).to_ical()
        event["summary"] = moon_phase(day.get("moonphase"))

        cal.add_component(event)

    return


def update_tidal_calendar(cal, payload, timezone=None):
    for tide_turn in payload["values"]:
        event = Event()
        dtstart = datetime.fromisoformat(tide_turn["time"])
        event["uid"] = int(dtstart.timestamp())
        event["dtstamp"] = vDatetime(dtstart).to_ical()
        event["dtstart"] = vDatetime(dtstart).to_ical()

        if tide_turn["value"] < 1:
            event["summary"] = "Low tide {} metres".format(tide_turn["value"])
        else:
            event["summary"] = "High tide {} metres".format(tide_turn["value"])

        if timezone:
            local_datetime = dtstart.astimezone(ZoneInfo(timezone))
            event["summary"] += local_datetime.strftime(" @ %-I:%M%p").lower()

        cal.add_component(event)

    return


def display(cal):
    return cal.to_ical().decode("utf-8").replace("\r\n", "\n")
