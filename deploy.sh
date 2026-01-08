#!/bin/sh

if [[ -z "$VIRTUAL_ENV" ]]; then
  echo You are not in a virtual environment. Cancelling build.
  exit 1
fi

echo Building dependencies…

rm -rf deploy/* lambda-bundle.zip
mkdir -p deploy
uv export --no-dev --no-hashes | uv pip install -r - --target deploy

cd deploy
zip -r ../lambda-bundle.zip .
cd -
zip lambda-bundle.zip lambda_function.py tidal_functions.py .env

echo Prepared lambda-bundle.zip
