from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.config import Settings
from api.routers import health, reviews
from api.services.inbox import LANDING_STATES


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the app. Importing this module does not create landing directories."""
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        landing = app.state.settings.landing_dir
        for state in LANDING_STATES:
            (landing / state).mkdir(parents=True, exist_ok=True)
        yield

    app = FastAPI(title="AI Review Triage", lifespan=lifespan)
    app.state.settings = settings
    app.include_router(health.router)
    app.include_router(reviews.router)
    return app


app = create_app()
