import json
import os
from datetime import date
from pathlib import Path

CACHE_BUCKET = os.getenv("CACHE_BUCKET")
_LOCAL_DIR = Path(os.getenv("CACHE_DIR", ".cache"))
_s3_client = None


def _s3():
    global _s3_client
    if _s3_client is None:
        import boto3
        _s3_client = boto3.client("s3")
    return _s3_client


def _key(source: str, lat: float, lon: float, dt: date) -> str:
    return f"{source}/{round(float(lat), 4)}_{round(float(lon), 4)}/{dt.strftime('%Y/%m/%d')}.json"


def get(source: str, lat, lon, dt: date) -> dict | None:
    if CACHE_BUCKET:
        from botocore.exceptions import ClientError
        try:
            obj = _s3().get_object(Bucket=CACHE_BUCKET, Key=_key(source, lat, lon, dt))
            return json.loads(obj["Body"].read())
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "NoSuchKey":
                return None
            raise
    path = _LOCAL_DIR / _key(source, lat, lon, dt)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


def put(source: str, lat, lon, dt: date, data: dict):
    if CACHE_BUCKET:
        _s3().put_object(
            Bucket=CACHE_BUCKET,
            Key=_key(source, lat, lon, dt),
            Body=json.dumps(data),
            ContentType="application/json",
        )
        return
    path = _LOCAL_DIR / _key(source, lat, lon, dt)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")
