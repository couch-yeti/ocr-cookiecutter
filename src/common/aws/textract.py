import os

import boto3


def text_detection(s3_key: str, job_key: str, client: boto3.client):

    response = client.start_document_text_detection(
        DocumentLocation={
            "S3Object": {
                "Bucket": os.environ["BUCKET_NAME"],
                "Name": s3_key,
            }
        },
        OutputConfig={
            "S3Bucket": os.environ["BUCKET_NAME"],
            "S3Prefix": "output/",
        },
        NotificationChannel={
            "SNSTopicArn": os.environ["SNS_TOPIC_ARN"],
            "RoleArn": os.environ["TEXTRACT_SNS_ARN"],
        },
    )
    return response


def doc_analysis(
    s3_key: str, ocr_config: list[str], job_key: str, client: boto3.client
):
    response = client.start_document_analysis(
        DocumentLocation={
            "S3Object": {
                "Bucket": os.environ["BUCKET_NAME"],
                "Name": s3_key,
            }
        },
        FeatureTypes=ocr_config,
        NotificationChannel={
            "SNSTopicArn": os.environ["SNS_TOPIC_ARN"],
            "RoleArn": os.environ["TEXTRACT_SNS_ARN"],
        },
        OutputConfig={
            "S3Bucket": os.environ["BUCKET_NAME"],
            "S3Prefix": "output/",
        },
    )

    return response


def start_ocr(
    s3_key: str,
    ocr_config: list[str],
    job_tag: str,
    session: boto3.Session = None,
):
    if not session:
        session = boto3._get_default_session()
    client = session.client("textract")
    if ocr_config:
        response = doc_analysis(s3_key, ocr_config, job_tag, client)
    else:
        response = text_detection(s3_key, job_tag, client)

    return response["JobId"]


def get_results(ocr_id: str, job_type: str, session: boto3.Session):
    """Loop through all pages of textract result and combine them"""
    if not session:
        session = boto3._get_default_session()

    client = session.client("textract")
    if job_type == "text":
        func = client.get_document_text_detection
    else:
        func = client.get_document_analysis
    response = func(JobId=ocr_id)
    if response.get("NextToken"):
        next_token = response["NextToken"]
        while next_token:
            response = func(JobId=ocr_id, NextToken=next_token)
            next_token = response.get("NextToken")
    return response
