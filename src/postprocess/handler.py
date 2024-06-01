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
    bucket = body["bucket"]["name"]
    key = event["Records"][0]["s3"]["object"]["key"]
    uid = key[1]

    return {"bucket": bucket, "key": key, "uid": uid}


def create_file_and_store(text: str, s3_key: str):
    """Zip and store text data in s3"""
    with open("file.txt", "w") as f:
        f.write(text)
    s3.put(file=f, s3_key=s3_key, bucket=os.environ["BUCKET_NAME"])
    return None


@logger.inject_lambda_context(log_event=True, clear_state=True)
def lambda_handler(event, context=None):
    """Revieve job update from textract through eventbridge, get and store result"""

    data = parse_event(event)
    table = dynamo.get_table()

    item = table.get_item(
        Key={"pk": data["uid"], "sk": "request"},
        ProjectionExpression="ocr_id, ocr_job_type, file_name",
    )["Item"]

    # get textract result
    text_result = textract.get_results(
        ocr_id=item["ocr_id"], ocr_job_type="analysis"
    )

    # upload
    create_file_and_store(
        text_result, f"output/{data['uid']}/{data['file_name']}_result.txt"
    )
