from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routers.auth import router as auth_router

app = FastAPI(
    title="DMARCBridge",
    description="DMARC report processing and management API",
    version="0.1.0"
)

app.include_router(auth_router)

app.mount("/", StaticFiles(directory="static", html=True), name="static")
