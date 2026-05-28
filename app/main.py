from fastapi import FastAPI

from api.routers.meta_router import router as meta_router

app = FastAPI()

app.include_router(meta_router)