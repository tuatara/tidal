T I D A L
=========


What
----

Fetches NIWA tide data and saves to ical format. Requires Python 3, probably a fairly recent version.

How
---

1. [Get yourself an API token](https://developer.niwa.co.nz) from NIWA.
1. Create an `.env` file with values for `API_KEY`, `LAT` and `LONG`. You may also choose to set your own values for `DAYS` (defaulting to 30) or, if you want, `HOST`, although this seems very NIWA-specific and probably not useful elsewhere.
1. Get your virtual environment in place: `python3 -m venv .venv --upgrade-deps`
1. And activate it: `. .venv/bin/activate`.

Generate a calendar locally
---------------------------

1. Install the dependencies (`pip install -r requirements-base.txt` etc).
1. Run `python3 main.py`.
1. The calendar will be saved to the directory as `tidal.ical`.

Deploy as a lambda function
---------------------------

1. Run `./deploy.sh`, which will create `lambda-bundle.zip`.
1. [Deploy it](https://docs.aws.amazon.com/lambda/latest/dg/python-package.html#python-package-create-update).

Note that you can override environment variables when you call the function by providing `lat`, `long` or `days` query string parameters.
