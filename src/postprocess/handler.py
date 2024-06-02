import json
import os

from aws_lambda_powertools import Logger
from dotenv import load_dotenv

from common.aws import dynamo, textract, s3


load_dotenv()
logger = Logger(
    service=os.environ["PROJECT_NAME"], level=os.getenv("LOG_LEVEL", "WARN")
)


def parse_event(event):
    """Receive message from eventbridge"""

    body = json.loads(event["Records"][0]["body"])
    message = json.loads(body["Message"])
    print(message)
    bucket = message["DocumentLocation"]["S3Bucket"]
    key = message["DocumentLocation"]["S3ObjectName"]
    uid = key.split("/")[1]

    return {"bucket": bucket, "key": key, "uid": uid}


def create_file_and_store(data: dict, s3_key: str):
    """Zip and store text data in s3"""
    file_path = "/tmp/file.json"
    with open(file_path, "w") as f:
        json.dump(data, f)
    s3.upload(
        file_path=file_path, s3_key=s3_key, bucket=os.environ["BUCKET_NAME"]
    )
    return None


# @logger.inject_lambda_context(log_event=True, clear_state=True)
def lambda_handler(event, context=None):
    """Revieve job update from textract through eventbridge, get and store result"""

    data = parse_event(event)
    table = dynamo.get_table(os.environ["TABLE_NAME"])

    item = table.get_item(
        Key={"pk": data["uid"], "sk": "request"},
        ProjectionExpression="ocr_id, ocr_job_type, document_name",
    )["Item"]

    document_name = item["document_name"].split(".")[0]
    # get textract result
    text_result = textract.get_results(
        ocr_id=item["ocr_id"], ocr_job_type=item["ocr_job_type"]
    )

    # upload
    create_file_and_store(
        data=text_result,
        s3_key=f"output/{data['uid']}/{document_name}_result.json",
    )
