from fastapi import APIRouter, HTTPException

from common.aws import dynamo, s3
from api import schema

router = APIRouter(prefix="/ocr", tags=["ocr"])


@router.post("/{uid}")
def start_ocr():

    return {"message": "OCR process started"}
