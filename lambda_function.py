import json
from os import getenv

from dotenv import load_dotenv
from icalendar import Calendar

from tidal_functions import fetch_data, update_calendar, display


load_dotenv()


def lambda_handler(event, context):
    print('Received event ', json.dumps(event, indent=2))

    API_KEY = getenv("API_KEY")
    LAT = event.get("queryStringParameters", {}).get('lat', getenv("LAT"))
    LONG = event.get("queryStringParameters", {}).get('long', getenv("LONG"))
    DAYS = event.get("queryStringParameters", {}).get('days', getenv("DAYS", 30))
    HOST = getenv("HOST", "https://api.niwa.co.nz/tides/data")

    cal = Calendar()
    cal.add('prodid', '-//Maliloes//Tidal//')
    cal.add('version', '2.0')

    response = fetch_data(API_KEY, HOST, LAT, LONG, DAYS)

    update_calendar(cal, response.json())

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "text/calendar",
            "Content-Disposition": "filename=\"tidal.ics\"",
        },
        "body": display(cal)
    }
