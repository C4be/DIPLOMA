from langchain_gigachat.chat_models import GigaChat
from langchain_openai import ChatOpenAI
from typing import Dict, Optional, Callable

from .errors import UnsupportedProviderError
from settings import agent_settings


# Загрузка API ключей и URL's
SBER_API_KEY = agent_settings.SBER_API_KEY
CLOUDRU_API_KEY = agent_settings.CLOUD_API_KEY
CLOUDRU_API_URL = agent_settings.CLOUDRU_API_URL


# Создание фабрик для каждого провайдера
def _sber_chat_factory(api_key: str, model: str, **kwargs):
    return GigaChat(
        credentials=api_key,
        model=model,
        verify_ssl_certs=False,
        **kwargs
    )


def _cloudru_chat_factory(api_key: str, model: str, **kwargs):
    return ChatOpenAI(
        api_key=api_key,
        base_url=CLOUDRU_API_URL,
        model=model,
        **kwargs
    )


# Реестр провайдеров и их моделей
_PROVIDER_REGISTRY: Dict[str, Dict[str, object]] = {
    "gigachat": {
        "factory": _sber_chat_factory,
        "default_model": "GigaChat-2",
    },
    "gigachat-pro": {
        "factory": _sber_chat_factory,
        "default_model": "GigaChat-2-pro",
    },
    "qwen": {
        "factory": _cloudru_chat_factory,
        "default_model": "Qwen/Qwen3-Coder-Next",
    },
    "glm": {
        "factory": _cloudru_chat_factory,
        "default_model": "zai-org/GLM-4.7",
    },
}


def get_llm(
    provider: str,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    **kwargs
):
    """
    Создает LLM клиент по имени провайдера.
    - provider: имя провайдера (например, 'gigachat', 'qwen', 'glm')
    - model: опциональная конкретная версия модели; если не указана, используется default
    - api_key: ключ API; если не указан, будет взят из окружения (SBER/CLOUD/QWEN)
    """
    if not provider:
        raise ValueError("provider is required")

    key = provider.lower()
    entry = _PROVIDER_REGISTRY.get(key)
    if entry is None:
        raise UnsupportedProviderError(f"Неподдерживаемый тип провайдера: {provider}")

    factory: Callable = entry["factory"]
    model_name = model or entry["default_model"]

    # Подбор api_key по провайдеру, если не передан явно
    if api_key is None:
        if key.startswith("giga"):
            api_key = SBER_API_KEY
        elif key in ("qwen", "glm"):
            api_key = CLOUDRU_API_KEY

    if api_key is None:
        raise ValueError(f"API key required for provider '{provider}'")

    return factory(api_key=api_key, model=model_name, **kwargs)


def get_llm_by_name(name: str):
    """
    Более удобные алиасы для часто используемых LLM-конфигураций.
    """
    match name:
        case "giga-lite":
            return get_llm(provider="gigachat")
        case "giga-pro":
            return get_llm(provider="gigachat-pro")
        case "qwen-coder":
            return get_llm(provider="qwen")
        case "glm":
            return get_llm(provider="glm")
        case _:
            raise UnsupportedProviderError(f"Unknown llm alias: {name}")


# Основной объект, который будет использоваться для взаимодействия с GPT
llm = get_llm_by_name(agent_settings.CONTAINER_LLM)

