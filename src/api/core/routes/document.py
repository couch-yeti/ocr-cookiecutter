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
    table = dynamo.get_table(os.environ["TABLE"])
    db_document = schema.make_db_schema(document)
    item = db_document({"uid": str(uuid4()), **document.model_dump_json()})
    table.put_item(Item=item.model_dump_json())

    return {
        "uid": item.uid,
        "url": s3.generate_presigned_url(
            uid=item.uid,
            document_name=document.name,
        ),
    }


@router.get("/")
def get_document(uid: str = None, document_name: str = None):
    """Get a document from the system"""
    table = dynamo.get_table(os.environ["TABLE"])
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

