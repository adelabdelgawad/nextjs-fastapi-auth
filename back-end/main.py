import os
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from routers import auth
from dotenv import load_dotenv
import logging
from src.middleware import TokenRenewalMiddleware
import logfire

# Load environment variables from .env file
load_dotenv()
ORIGINS = os.getenv("ORIGINS")

logfire.configure()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] | [%(funcName)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


# Initialize FastAPI app with custom lifespan
app = FastAPI()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )


# Configure CORS middleware
# Middleware for CORS and infoging
origins = [
    ORIGINS,  # Frontend URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Explicitly specify allowed origins
    allow_credentials=True,  # Allow cookies and credentials
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

app.add_middleware(TokenRenewalMiddleware)


logfire.instrument_fastapi(app, capture_headers=True)

# Include additional routers
app.include_router(auth.router, tags=["Authentication"])
