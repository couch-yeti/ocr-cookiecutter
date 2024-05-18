import json


def event_parser(event: dict[str, str]) -> dict:
    """Expecting an event aws s3 trigger event and returns the parsed data"""

    body = json.loads(event["Records"][0]["body"])
    return {
        "bucket": body["bucket"]["name"],
        "key": body["object"]["key"],
    }

def lambda_handler(event: dict, context: dict) -> dict:
    """Lambda handler function"""

    parsed_data = event_parser(event)
    
    return parsed_data