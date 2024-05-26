import os

import boto3

boto3.setup_default_session(region_name="us-west-2")

os.environ["TABLE"] = "OCR-API-Table710B521B-1Z0XFT3D77PU"
os.environ["BUCKET"] = "ocr-api-bucket83908e77-5elc2h9you44"

import handler

print(
    handler.lambda_handler(event={"document_name": "my_doc.pdf"}, context=None)
)
# my_doc = schema.Document(document_name="my_doc.pdf")
# print(document.upload_document(my_doc))
