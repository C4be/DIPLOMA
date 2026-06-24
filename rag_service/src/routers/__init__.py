from .files_router import router as files_router

def get_all_routers():
    return [
        files_router
    ]

__all__ = [
    "get_all_routers"
]