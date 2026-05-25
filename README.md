T I D A L
=========


What
----

Fetches NIWA tide data and saves to ical format.

And for a bonus, also fetches astronomical data from Visual Crossing.

API responses are cached per-day so repeat runs avoid redundant API calls.

Requires at least python 3.10, and uv.

How
---

1. Get yourself [an API token](https://developer.niwa.co.nz) from NIWA
1. Get yourself [another API token](https://www.visualcrossing.com/account) from Visual Crossing
1. Create an `.env` file with values for `NIWA_API_KEY`, `VISUAL_CROSSING_API_KEY`, `LAT` and `LONG`. You may also choose to set your own value for `DAYS` (defaulting to 30).
1. Get your virtual environment in place: `uv venv`
1. And activate it: `. .venv/bin/activate`.
1. If you’d like a localised time included in the tides event description, then add a `TIMEZONE` value in your `.env` file, e.g. "Pacific/Auckland".

Generate a calendar locally
---------------------------

1. Install the dependencies (`uv sync`)
1. `uv run main.py`.
1. The calendar will be saved to the directory as `tidal.ics`

Fetched data is cached to `.cache/` so subsequent runs only call the APIs for days not already stored locally.

Deploy as a lambda function
---------------------------

1. Run `./deploy.sh`, which will create `lambda-bundle.zip`.
1. [Deploy it](https://docs.aws.amazon.com/lambda/latest/dg/python-package.html#python-package-create-update).
1. Create an S3 bucket for the cache and add a `CACHE_BUCKET` environment variable to the Lambda with the bucket name.
1. Ensure the Lambda execution role has `s3:GetObject` and `s3:PutObject` on `arn:aws:s3:::your-bucket/*` and `s3:ListBucket` on `arn:aws:s3:::your-bucket`. All three are required — without `s3:ListBucket`, S3 returns `403 AccessDenied` instead of `404` for cache misses.

Note that you can override environment variables when you call the function by providing `lat`, `long` or `days` query string parameters.
