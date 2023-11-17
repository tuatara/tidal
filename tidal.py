from datetime import datetime
from os import getenv

from dotenv import load_dotenv
from icalendar import Calendar, Event, vDatetime
import requests


cal = Calendar()

load_dotenv()


def fetch_data():
    API_KEY = getenv("API_KEY")
    LAT = getenv("LAT")
    LONG = getenv("LONG")
    DAYS = getenv("DAYS", 30)
    HOST = getenv("HOST", "https://api.niwa.co.nz/tides/data")

    HEADERS = {
        "x-apikey": API_KEY,
    }
    QUERY = {
        "lat": LAT,
        "long": LONG,
        "numberOfDays": DAYS,
    }
    return requests.get(HOST, headers=HEADERS, params=QUERY)


def update_calendar(cal, payload):
    for value in payload['values']:
        event = Event()
        dtstart = datetime.fromisoformat(value['time'])
        event['uid'] = int(dtstart.timestamp())
        event['dtstamp'] = vDatetime(dtstart).to_ical()
        event['dtstart'] = vDatetime(dtstart).to_ical()

        if value['value'] < 1:
            event['summary'] = "Low tide {} metres".format(value['value'])
        else:
            event['summary'] = "High tide {} metres".format(value['value'])

        cal.add_component(event)

    return


def display(cal):
    return cal.to_ical().decode("utf-8").replace('\r\n', '\n')


def __run__():
    response = fetch_data()

    cal = Calendar()
    cal.add('prodid', '-//Maliloes//Tidal//')
    cal.add('version', '2.0')

    update_calendar(cal, response.json())

    with open('tidal.ics', 'w', encoding="utf-8") as f:
        f.write(display(cal))

    print('OK')


__run__()
