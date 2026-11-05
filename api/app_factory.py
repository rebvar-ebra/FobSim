"""Build independent API applications without initializing a database."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def create_app() -> FastAPI:
    # Keep the existing backend import convention used by server.py and uvicorn.
    from server import router

    app = FastAPI(title="FobSim API", version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins in development
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    app.include_router(router)
    return app
