from app.core.config import get_settings
from app.services.providers.base import ProviderAdapter
from app.services.providers.mock import MockProviderAdapter


def get_provider_adapter() -> ProviderAdapter:
    settings = get_settings()
    if settings.provider_mode == "mock":
        return MockProviderAdapter()
    return MockProviderAdapter()
