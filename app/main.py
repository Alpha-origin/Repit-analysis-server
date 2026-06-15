from fastapi import FastAPI

from api.routers.interview_router import router as interview_router
from api.routers.meta_router import router as meta_router

app = FastAPI()

app.include_router(meta_router)
app.include_router(interview_router)
