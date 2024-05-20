from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from routes import document, ocr

app = FastAPI()
app.add_route()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def lambda_handler(event, context=None):
    handler = Mangum(app)
    return handler(event=event, context=context)
