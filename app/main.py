from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import __version__
from app.api.routes_approvals import router as approvals_router
from app.api.routes_runs import router as runs_router
from app.connectors import demo_connectors
from app.core.config import get_settings
from app.core.sentry_setup import configure_sentry
from app.state.repository import SQLiteRunRepository

settings = get_settings()
repository = SQLiteRunRepository(settings.database_url)
connectors = demo_connectors()


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_sentry(settings.sentry_dsn, settings.app_env)
    yield


app = FastAPI(
    title="AI Delivery Control Plane",
    summary="Turn AI requests into approved, auditable delivery workflows.",
    description=(
        "A human-in-the-loop control plane that classifies business AI requests, drafts "
        "solution briefs, enforces approval before external writes, and creates traceable "
        "delivery artifacts. Connector calls run in safe demo mode by default."
    ),
    version=__version__,
    lifespan=lifespan,
    license_info={"name": "MIT", "identifier": "MIT"},
    openapi_tags=[
        {
            "name": "1. Request Intake",
            "description": (
                "Submit a business AI request, inspect its classification and solution brief, "
                "then check the workflow's current state."
            ),
        },
        {
            "name": "2. Human Approval",
            "description": (
                "Record an explicit human decision before the control plane can perform any "
                "external write action."
            ),
        },
        {
            "name": "3. Approved Execution",
            "description": (
                "Execute the approved delivery plan and return the generated repository, issue, "
                "and notification artifacts."
            ),
        },
        {
            "name": "Service Health",
            "description": "Confirm that the API is available and inspect its active runtime mode.",
        },
    ],
)
app.include_router(runs_router)
app.include_router(approvals_router)


@app.get(
    "/health",
    tags=["Service Health"],
    summary="Check service health",
    description="Returns the application version, environment, and active connector mode.",
    operation_id="check_service_health",
)
async def health() -> dict:
    return {
        "service": "ai-delivery-control-plane",
        "version": __version__,
        "status": "ok",
        "environment": settings.app_env,
        "connector_mode": settings.connector_mode,
    }
