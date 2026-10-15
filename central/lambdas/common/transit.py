"""Presigned URLs for the S3 transit bucket. The object key is the transfer ID (random, no
filename). Only Bucket and Key are signed, so the owner's agent may send any (or no)
Content-Type and Content-Length on the PUT. Presigning is local: it needs no network."""
import datetime
import os

_client = None


def upload_url_expiry_seconds():
    return int(os.environ.get("UPLOAD_URL_EXPIRY_SECONDS", "600"))


def download_url_expiry_seconds():
    return int(os.environ.get("DOWNLOAD_URL_EXPIRY_SECONDS", "300"))


def _s3():
    global _client
    if _client is None:
        import boto3
        from botocore.config import Config

        region = os.environ.get("AWS_REGION", "us-east-1")
        # SigV4 plus the regional endpoint: no signature-version surprises or redirects.
        _client = boto3.client("s3", region_name=region, endpoint_url=f"https://s3.{region}.amazonaws.com",
                               config=Config(signature_version="s3v4"))
    return _client


def _presign(method, key, seconds):
    url = _s3().generate_presigned_url(
        method, Params={"Bucket": os.environ["TRANSIT_BUCKET"], "Key": key}, ExpiresIn=seconds)
    expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=seconds)
    return url, expires_at


def presign_put(key):
    """(url, expires_at) for the owner to upload the file."""
    return _presign("put_object", key, upload_url_expiry_seconds())


def presign_get(key):
    """(url, expires_at) for the requester to download the file."""
    return _presign("get_object", key, download_url_expiry_seconds())


DELETE_BATCH = 1000  # the S3 DeleteObjects API limit


def delete_objects(keys):
    """Delete transit objects. Returns (keys S3 reports deleted, number of keys that failed).
    A key that is already gone counts as deleted, so repeating a call is safe."""
    deleted, errors = set(), 0
    for start in range(0, len(keys), DELETE_BATCH):
        batch = keys[start:start + DELETE_BATCH]
        result = _s3().delete_objects(Bucket=os.environ["TRANSIT_BUCKET"],
                                      Delete={"Objects": [{"Key": key} for key in batch]})
        deleted.update(item["Key"] for item in result.get("Deleted", []))
        errors += len(result.get("Errors", []))
    return deleted, errors
