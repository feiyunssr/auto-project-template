from apps.backend.core.config import get_settings
from apps.backend.services.providers.base import ProviderAdapter
from apps.backend.services.providers.mock import MockProviderAdapter


def get_provider_adapter() -> ProviderAdapter:
    settings = get_settings()
    if settings.provider_mode == "mock":
        return MockProviderAdapter()
    return MockProviderAdapter()
