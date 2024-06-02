import os

import boto3


def upload(
    file_path: str, s3_key: str, bucket: str, session: boto3.Session = None
):
    """Upload file to s3"""
    if not session:
        session = boto3._get_default_session()
    client = session.client("s3")

    client.upload_file(file_path, bucket, s3_key)


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
    s3_key: str,
    bucket_name: str,
    method: str = "put",
    session: boto3.Session = None,
):

    client_method = {"get": "get_object", "put": "put_object"}
    if not session:
        session = boto3._get_default_session()
    s3 = session.client("s3")
    url = s3.generate_presigned_url(
        ClientMethod=client_method[method.lower()],
        Params={
            "Bucket": bucket_name,
            "Key": s3_key,
            "ContentType": "application/pdf",
        },
        ExpiresIn=60,
    )
    return url
