import boto3


def upload_file(
    file_path: str, bucket_name: str, session: boto3.Session = None
):
    if not session:
        session = boto3._get_default_session()
    s3 = session.resource("s3")
    bucket = s3.Bucket(bucket_name)
    with open(file_path, "rb") as f:
        bucket.upload_fileobj(f, file_path.split("/")[-1])


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
        expires_in=30,
    )
    return url
