from datetime import datetime

from pydantic import BaseModel, Field, create_model

now = datetime.now()


def make_db_schema(base_model: type):
    """function adds mixin fields dynamically to be used in customer facing
    models
    """
    BaseModel.model_fields
    name = f"{base_model.__name__}DB"
    fields = {}
    for model in [base_model, Mixin]:
        fields_ = {
            field_name: (field.annotation, field.default)
            for field_name, field in model.model_fields.items()
        }
        fields.update(fields_)

    return create_model(name, **fields)


class Mixin(BaseModel):
    uid: str = Field(description="The unique identifier of the item")
    created_at: str = Field(
        description="The date and time the item was created"
    )
    updated_at: str = Field(
        description="The date and time the item was last updated",
        default=now.strftime("%d-%m-%Y %H:%M:%S"),
    )
    expiration: int = Field(
        description="The expiration time of the item described as an integer"
    )


class Document(BaseModel):
    document_name: str = Field(description="The name of the document")
