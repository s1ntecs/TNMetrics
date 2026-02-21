from fastapi import FastAPI

from src.presentation.api.routes_auth import router as auth_router
from src.presentation.api.routes_metrics import router as metrics_router
from src.presentation.api.routes_records import router as records_router
from src.presentation.api.routes_tags import router as tags_router

app = FastAPI(title="Metrics API")

app.include_router(auth_router)
app.include_router(metrics_router)
app.include_router(tags_router)
app.include_router(records_router)


@app.get("/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
