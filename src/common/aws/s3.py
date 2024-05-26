import os

import boto3


def put(file, s3_key, bucket: str, session: boto3.Session = None):
    """Upload file to s3"""
    if not session:
        session = boto3._get_default_session()
    client = session.client("s3")

    client.put_object(Bucket=bucket, Key=s3_key, Body=file)


def download_file(
    s3_key: str,
    file_path: str,
    bucket_name: str,
    session: boto3.Session = None,
):
    if not session:
        session = boto3._get_default_session()
    s3 = session.resource("s3")
    bucket = s3.Bucket(bucket_name)
    bucket.download_file(s3_key, file_path)


def get_file_data(
    s3_key: str, bucket_name: str, session: boto3.Session = None
):
    if not session:
        session = boto3._get_default_session()
    s3 = session.resource("s3")
    bucket = s3.Bucket(bucket_name)
    obj = bucket.Object(s3_key)
    return obj.get()["Body"].read().decode("utf-8")


def generate_presigned_url(
    uid: str,
    document_name: str,
    bucket_name: str,
    method: str = "put",
    session: boto3.Session = None,
):
    s3_key = f"input/{uid}/{document_name}"
    client_method = {"get": "get_object", "put": "put_object"}
    if not session:
        session = boto3._get_default_session()
    s3 = session.client("s3")
    url = s3.generate_presigned_url(
        ClientMethod=client_method[method.lower()],
        Params={
            "Bucket": bucket_name,
            "Key": s3_key,
        },
        ExpiresIn=30,
    )
    return url
