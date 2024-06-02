from datetime import datetime

from pydantic import BaseModel, Field, field_validator

now = datetime.now()


class BaseRecord(BaseModel):
    pk: str = Field(description="Database partition key")
    sk: str = Field(description="Database sort key")
    uid: str = Field(description="The unique identifier of the item")
    created_at: str = Field(
        description="The date and time the item was created",
        default=now.strftime("%d-%m-%Y %H:%M:%S"),
    )

    updated_at: str = Field(
        description="The date and time the item was last updated",
        default=now.strftime("%d-%m-%Y %H:%M:%S"),
    )
    expiration: int = Field(
        description="The expiration time of the item described as an integer",
        # timestamp int from now plus 3 days
        default=int((now.timestamp() + 259200)),
    )


class Document(BaseModel):
    document_name: str = Field(description="The name of the document")
    ocr_config: list[str] = Field(
        description="A list of Textract options which can include tables, forms etc",
        default=[],
    )

    # validator for ocr_config to ensure only tables, and forms are valid options
    @field_validator("ocr_config")
    def validate_ocr_config(cls, v):
        if not v:
            return v
        if v and not all([i in ["tables", "forms"] for i in v]):
            raise ValueError("Invalid ocr_config options")
        return v
