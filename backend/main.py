# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .db import init_db
from .routers import trajectory
from .utils.logger import log_request_middleware, logger
import uvicorn

app = FastAPI(title="Autonomous Wall Finisher Backend", version="0.1")

# CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# initialize DB on startup
@app.on_event("startup")
async def startup():
    init_db()
    logger.info("Database initialized")

# include routers
app.include_router(trajectory.router)

# add logging middleware
app.middleware("http")(log_request_middleware)

# simple health-check
@app.get("/health")
async def health():
    return {"status":"ok"}

# If you run backend/main.py directly, start uvicorn
if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
