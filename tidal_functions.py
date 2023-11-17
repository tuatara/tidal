from datetime import datetime

from icalendar import Event, vDatetime
import requests


def fetch_data(api_key, host, lat, long, days=30):
    HEADERS = {
        "x-apikey": api_key,
    }
    QUERY = {
        "lat": lat,
        "long": long,
        "numberOfDays": days,
    }
    return requests.get(host, headers=HEADERS, params=QUERY)


def update_calendar(cal, payload):
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

        cal.add_component(event)

    return


def display(cal):
    return cal.to_ical().decode("utf-8").replace('\r\n', '\n')
