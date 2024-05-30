import os
from uuid import uuid4

from boto3.dynamodb.conditions import Key
from fastapi import APIRouter, HTTPException

from core.data import schema
from common.aws import dynamo, s3

router = APIRouter(prefix="/document", tags=["document"])


@router.post("/")
def upload_document(document: schema.Document):
    """Upload a document to the system"""
    table = dynamo.get_table(os.environ["TABLE_NAME"])

    uid = str(uuid4())
    s3_key = f"input/{uid}/{document.document_name}"
    db_data = schema.BaseRecord(pk=uid, sk="request", uid=uid)
    item = {**db_data.model_dump(), **document.model_dump()}
    table.put_item(Item=item)

    return {
        "uid": item["uid"],
        "url": s3.generate_presigned_url(
            s3_key=s3_key,
            document_name=document.document_name,
            bucket_name=os.environ["BUCKET_NAME"],
        ),
    }


@router.get("/")
def get_document(uid: str = None, document_name: str = None):
    """Get a document from the system"""
    table = dynamo.get_table(os.environ["TABLE_NAME"])
    key = (
        Key("pk").eq(uid) & Key("sk").eq("document")
        if uid
        else Key("pk").eq(document_name)
    )
    items = table.query(
        KeyConditionExpression=key,
        ProjectionExpression="uid, document_name",
        IndexName="document-index" if uid else None,
    )["Items"]
    if not items:
        raise HTTPException(
            status_code=404,
            detail="There's no document associted with the provided identifier",
        )
    item = items[0]
    return {
        "url": s3.generate_presigned_url(
            uid=item["uid"], document_name=item["document_name"], method="get"
        )
    }
