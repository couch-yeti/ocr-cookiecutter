import os
import json

from common.aws import dynamo, textract


def parse_event(event):
    """Function receives a trigger from s3 to get the object key and bucket name"""
    body = json.loads(event["Records"][0]["body"])
    bucket = body["bucket"]["name"]
    key = event["Records"][0]["s3"]["object"]["key"]
    uid = key[1]

    return {"bucket": bucket, "key": key, "uid": uid}


def lambda_handler(event, context=None):

    data = parse_event(event)
    table = dynamo.get_table()

    # get data from dynamodb
    item = table.get_item(
        Key={"pk": data["uid"], "sk": "request"},
        ProjectionExpression="ocr_config",
    )["Item"]
    data.update(**item)

    # start text extraction
    textract.start_ocr(
        s3_key=data["key"],
        ocr_config=data.get("ocr_config"),
        job_tag=data["uid"],
    )
