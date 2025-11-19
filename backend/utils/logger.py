# backend/utils/logger.py
import logging
import time
from fastapi import Request

logger = logging.getLogger("wallfinisher")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

# simple request timing middleware to include in app
async def log_request_middleware(request: Request, call_next):
    start = time.time()
    try:
        response = await call_next(request)
        return response
    finally:
        elapsed = (time.time() - start) * 1000.0
        logger.info(f"{request.client.host if request.client else 'unknown'} {request.method} {request.url.path} {response.status_code if 'response' in locals() else '??'} {elapsed:.1f}ms")
