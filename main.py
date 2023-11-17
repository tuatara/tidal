from os import getenv

from dotenv import load_dotenv
from icalendar import Calendar

from tidal_functions import fetch_data, update_calendar, display


load_dotenv()


def __run__():
    API_KEY = getenv("API_KEY")
    LAT = getenv("LAT")
    LONG = getenv("LONG")
    DAYS = getenv("DAYS", 30)
    HOST = getenv("HOST", "https://api.niwa.co.nz/tides/data")

    cal = Calendar()
    cal.add('prodid', '-//Maliloes//Tidal//')
    cal.add('version', '2.0')

    response = fetch_data(API_KEY, HOST, LAT, LONG, DAYS)

    update_calendar(cal, response.json())

    with open('tidal.ics', 'w', encoding="utf-8") as f:
        f.write(display(cal))

    print('OK')


__run__()
