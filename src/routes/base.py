from fastapi import APIRouter
import os
base_router = APIRouter(
    prefix="/api/v1",
    tags=["api_v1"],
)

@base_router.get("/hello")
async def root():
    app_name = os.getenv("APP_NAME")
    return {"message": f"Hello World, {app_name}!"}