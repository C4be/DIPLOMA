import os
import uvicorn
from fastapi import FastAPI

from api.routers import base_router, giga_router
from logger import Logger
from settings import agent_settings


__logger = Logger(name="main")

def get_application() -> FastAPI:
    application = FastAPI(
        title="ИИ TextToSQL агент",
        debug=agent_settings.DEBUG
    )

    application.include_router(base_router)
    application.include_router(giga_router)

    return application


app = get_application()
__logger.info(f"Приложение {app.title} успешно запущено!")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", reload=True)