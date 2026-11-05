"""Build independent API applications without initializing a database."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.runtime_config import load_runtime_config


def create_app() -> FastAPI:
    config = load_runtime_config()
    # Keep the existing backend import convention used by server.py and uvicorn.
    from server import router
    from api.routes.projects import router as projects_router
    from api.routes.experiments import router as experiments_router
    from api.routes.runs import router as runs_router

    app = FastAPI(title="FobSim API", version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[config.frontend_origin],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    app.include_router(router)
    app.include_router(projects_router)
    app.include_router(experiments_router)
    app.include_router(runs_router)
    return app
