#!/usr/bin/env bash
set -euo pipefail

python_version=3.14
target_platform=x86_64-manylinux_2_28

echo Building dependencies...

rm -rf deploy/* lambda-bundle.zip
mkdir -p deploy
uv export --no-dev --no-hashes | uv pip install -r - --target deploy \
  --python-version "$python_version" \
  --python-platform "$target_platform"

(
  cd deploy
  zip -qr ../lambda-bundle.zip .
)
zip -q lambda-bundle.zip lambda_function.py tidal_functions.py cache.py

echo Prepared lambda-bundle.zip
