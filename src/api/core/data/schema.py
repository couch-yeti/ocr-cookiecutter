from datetime import datetime

from pydantic import BaseModel, Field, create_model

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
