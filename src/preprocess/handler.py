import os
import json

from aws_lambda_powertools import Logger
from dotenv import load_dotenv

from common.aws import dynamo, textract

load_dotenv()
logger = Logger(
    service=os.environ["PROJECT_NAME"], level=os.getenv("LOG_LEVEL", "WARN")
)


def parse_event(event):
    """Function receives a trigger from s3 to get the object key and bucket name"""
    body = event["Records"][0]["s3"]
    bucket = body["bucket"]["name"]
    key = body["object"]["key"]
    uid = key.split("/")[1]

    return {"bucket": bucket, "key": key, "uid": uid}


@logger.inject_lambda_context(log_event=True, clear_state=True)
def lambda_handler(event, context=None):

    data = parse_event(event)
    table = dynamo.get_table(os.environ["TABLE_NAME"])

    # get data from dynamodb
    item = table.get_item(
        Key={"pk": data["uid"], "sk": "request"},
        ProjectionExpression="ocr_config",
    )["Item"]
    data.update(**item)

    # start text extraction
    ocr_id = textract.start_ocr(
        s3_key=data["key"],
        ocr_config=data.get("ocr_config"),
        job_tag=data["uid"],
    )
    table.update_item(
        Key={"pk": data["uid"], "sk": "request"},
        UpdateExpression="SET ocr_status = :s, ocr_id = :i",
        ExpressionAttributeValues={":s": "processing", ":i": ocr_id},
    )
