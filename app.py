import os

import aws_cdk as cdk
from dotenv import load_dotenv

from infra import stack


load_dotenv()

app = cdk.App()
context = app.node.get_all_context()

stack = stack.Main(app, "OCR-API")
tags = {"application": "ocr-api", "environment": os.environ["ENVIRONMENT"]}
for tag, value in tags.items():
    cdk.Tags.of(stack).add(tag, value)

app.synth()
