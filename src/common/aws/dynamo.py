import boto3


def get_table(table_name: str, session: boto3.Session = None):
    if not session:
        session = boto3._get_default_session()
    resource = session.resource("dynamodb")
    return resource.Table(table_name)
