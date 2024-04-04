T I D A L
=========


What
----

Fetches NIWA tide data and saves to ical format.

And for a bonus, also fetches astronomical data from Visual Crossing.

Requires at least Python 3.10.

How
---

1. Get yourself [an API token](https://developer.niwa.co.nz) from NIWA.
1. Get yourself [another API token](https://www.visualcrossing.com/account) from Visual Crossing.
1. Get your virtual environment in place: `python3 -m venv .venv --upgrade-deps`.
1. And activate it: `. .venv/bin/activate`.
1. Create an `.env` file with values for `NIWA_API_KEY`, `VISUAL_CROSSING_API_KEY`, `LAT` and `LONG`. You may also choose to set your own value for `DAYS` (defaulting to 30).
1. If you’d like a localised time included in the tides event description, then add a `TIMEZONE` value in your `.env` file, e.g. "Pacific/Auckland".

Generate a calendar locally
---------------------------

1. Install the dependencies (`pip install -r requirements-base.txt` etc).
1. Run `python3 main.py`.
1. The calendar will be saved to the directory as `tidal.ics`.

Deploy as a lambda function
---------------------------

1. Run `./deploy.sh`, which will create `lambda-bundle.zip`.
1. [Deploy it](https://docs.aws.amazon.com/lambda/latest/dg/python-package.html#python-package-create-update).

Note that you can override environment variables when you call the function by providing `lat`, `long` or `days` query string parameters.
