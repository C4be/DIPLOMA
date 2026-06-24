from fastapi import APIRouter

base_router = APIRouter()

@base_router.get('/')
def get_root():
    return {
        "message": "Hello from FastAPI GigaChat Agent"
    }