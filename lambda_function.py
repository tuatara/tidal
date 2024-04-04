import json
from os import getenv

from dotenv import load_dotenv
from icalendar import Calendar

from tidal_functions import fetch_astro_data, fetch_tidal_data, update_astro_calendar, update_tidal_calendar, display


load_dotenv()


def lambda_handler(event, context):
    print('Received event ', json.dumps(event, indent=2))

    NIWA_API_KEY = getenv("NIWA_API_KEY", None)
    VISUAL_CROSSING_API_KEY = getenv("VISUAL_CROSSING_API_KEY")
    LAT = event.get("queryStringParameters", {}).get('lat', getenv("LAT"))
    LONG = event.get("queryStringParameters", {}).get('long', getenv("LONG"))
    DAYS = event.get("queryStringParameters", {}).get('days', getenv("DAYS", 30))
    TIMEZONE = getenv("TIMEZONE", None)

    cal = Calendar()
    cal.add('prodid', '-//Maliloes//Tidal//')
    cal.add('version', '2.0')

    if VISUAL_CROSSING_API_KEY:
        astro_response = fetch_astro_data(VISUAL_CROSSING_API_KEY, LAT, LONG, DAYS)
        update_astro_calendar(cal, astro_response.json())

    if NIWA_API_KEY:
        tidal_response = fetch_tidal_data(NIWA_API_KEY, LAT, LONG, DAYS)
        update_tidal_calendar(cal, tidal_response.json(), TIMEZONE)

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "text/calendar",
            "Content-Disposition": "filename=\"tidal.ics\"",
        },
        "body": display(cal)
    }
