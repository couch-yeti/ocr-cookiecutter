import os

from aws_lambda_powertools import Logger
from dotenv import load_dotenv
from mangum import Mangum

from core.config import app

load_dotenv()
logger = Logger(
    serivce=os.environ["PROJECT_NAME"],
    level=os.environ.get("LOG_LEVEL", "WARN"),
)


@logger.inject_lambda_context(log_event=True, clear_state=True)
def lambda_handler(event, context=None):
    handler = Mangum(app)
    return handler(event=event, context=context)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
