from core.data import schema
from core.routes import document


my_doc = schema.Document(document_name="my_doc.pdf")
print(document.upload_document(my_doc))
