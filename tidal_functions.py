from datetime import datetime
import pytz

from icalendar import Event, vDatetime
import requests


def moon_phase(grade):
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


def fetch_astro_data(api_key, lat, long, days=30):
    HEADERS = {}
    QUERY = {
        "key": api_key,
        "include": "days",
        "elements": "datetime,moonphase,moonrise",
        "timezone": "UTC",
    }
    ENDPOINT = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{},{}/next{}days".format(lat, long, days)

    return requests.get(ENDPOINT, headers=HEADERS, params=QUERY)


def fetch_tidal_data(api_key, lat, long, days=30):
    HEADERS = {
        "x-apikey": api_key,
    }
    QUERY = {
        "lat": lat,
        "long": long,
        "numberOfDays": days,
    }
    ENDPOINT = "https://api.niwa.co.nz/tides/data"

    return requests.get(ENDPOINT, headers=HEADERS, params=QUERY)


def update_astro_calendar(cal, payload):
    for day in payload['days']:
        if not day.get('moonrise', False):
            continue
        event = Event()

        dtstart = datetime.strptime("{} {}".format(day['datetime'], day['moonrise']), "%Y-%m-%d %H:%M:%S").astimezone(pytz.timezone(payload['timezone']))
        event['uid'] = int(dtstart.timestamp())
        event['dtstamp'] = vDatetime(dtstart).to_ical()
        event['dtstart'] = vDatetime(dtstart).to_ical()
        event['summary'] = moon_phase(day.get('moonphase'))

        cal.add_component(event)

    return


def update_tidal_calendar(cal, payload, timezone=None):
    for tide_turn in payload['values']:
        event = Event()
        dtstart = datetime.fromisoformat(tide_turn['time'])
        event['uid'] = int(dtstart.timestamp())
        event['dtstamp'] = vDatetime(dtstart).to_ical()
        event['dtstart'] = vDatetime(dtstart).to_ical()

        if tide_turn['value'] < 1:
            event['summary'] = "Low tide {} metres".format(tide_turn['value'])
        else:
            event['summary'] = "High tide {} metres".format(tide_turn['value'])

        if timezone:
            local_datetime = dtstart.astimezone(pytz.timezone(timezone))
            event['summary'] += local_datetime.strftime(' @ %-I:%M%p').lower()

        cal.add_component(event)

    return


def display(cal):
    return cal.to_ical().decode("utf-8").replace('\r\n', '\n')
