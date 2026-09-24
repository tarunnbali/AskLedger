import logging

import openai
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.rate_limit import limiter

from app.api.v1.auth import router as auth_router
from app.api.v1.chat import router as chat_router
from app.api.v1.health import router as health_router

logger = logging.getLogger("askledger")

app = FastAPI(title=settings.PROJECT_NAME)

# Rate limiting — protects the free LLM quota on a public demo deployment.
# chat.py applies settings.CHAT_RATE_LIMIT to the /chat endpoint specifically.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# LLM failures (e.g. the free-tier daily quota running out) would otherwise be
# unhandled 500s without CORS headers, which browsers misreport as CORS errors.
@app.exception_handler(openai.RateLimitError)
async def llm_quota_handler(request: Request, exc: openai.RateLimitError):
    return JSONResponse(
        status_code=503,
        content={"detail": "The demo has used up its free AI quota for now. Please try again later."},
    )


@app.exception_handler(openai.APIError)
async def llm_error_handler(request: Request, exc: openai.APIError):
    return JSONResponse(
        status_code=502,
        content={"detail": "The AI service is temporarily unavailable. Please try again in a moment."},
    )


# Anything else unhandled: log the traceback and return JSON. Registered before
# CORSMiddleware so CORS wraps it — otherwise the 500 lacks CORS headers and
# browsers report a misleading CORS error instead of the real failure.
@app.middleware("http")
async def catch_unhandled_errors(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as exc:
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Something went wrong on the server. Please try again.",
                "error_type": type(exc).__name__,
            },
        )


# Add CORS middleware — origins come from ALLOWED_ORIGINS in .env so the
# deployed frontend URL can be added without touching code.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(chat_router, prefix="/api/v1", tags=["chat"])
app.include_router(health_router, prefix="/api/v1", tags=["health"])
