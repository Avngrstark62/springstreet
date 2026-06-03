from fastapi import FastAPI

from config import settings
from router import router

app = FastAPI(title=settings.app_name)
app.include_router(router)
