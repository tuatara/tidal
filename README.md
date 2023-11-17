T I D A L
=========


What
----

Fetches NIWA tide data and saves to ical format

How
---

1. Get yourself an API token from https://developer.niwa.co.nz
1. Create an `.env` file with values for `API_KEY`, `LAT` and `LONG`. You may also choose to set your own values for `DAYS` (defaulting to 30) or, if you want, `HOST`, although this seems very NIWA-specific and probably not useful elsewhere.
1. Instation the dependencies (`pip install -r requirements-base.txt` etc). A virtualenv is obviously recommended.
1. Run `python3 tidal.py`

Requires Python 3, probably a fairly recent version.
