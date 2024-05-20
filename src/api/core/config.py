from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from common.log import get_child_logger
from routes import itinerary, trips

logger = get_child_logger()
app = FastAPI(
    docs_url="/swagger/ui",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_headers=["*"],
    allow_methods=["*"],
)


class ExceptionLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except HTTPException as he:
            logger.error(f"Exception: {he.status_code}", exc_info=True)
            return JSONResponse(
                context={"detail": he.detail}, status_code=he.status_code
            )

        except Exception as e:
            logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
            return JSONResponse(
                content={"detail": "internal server error"}, status_code=500
            )


app.include_router(trips.router)
app.include_router(itinerary.router)
app.add_middleware(ExceptionLoggingMiddleware)
