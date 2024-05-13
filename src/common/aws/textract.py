import os

import boto3


def start_text_extraction(
    bucket_name: str, file_name: str, session: boto3.Session = None
):
    if not session:
        session = boto3._get_default_session()
    client = session.client("textract")
    response = client.start_document_text_detection(
        DocumentLocation={
            "S3Object": {
                "Bucket": os.environ["BUCKET_NAME"],
                "Name": file_name,
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
    return response["JobId"]
