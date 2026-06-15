from fastapi import FastAPI

from app.api.routers.interview_router import router as interview_router
from app.api.routers.meta_router import router as meta_router

app = FastAPI()

app.include_router(meta_router)
app.include_router(interview_router)
