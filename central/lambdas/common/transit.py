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
