"""⚙️ Configuration via environment variables / .env file."""

from pydantic import HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class NetBoxSettings(BaseSettings):
    """NetBox connection settings.

    Reads from environment variables or a .env file in the project root.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="NETBOX_",
        case_sensitive=False,
    )

    url: HttpUrl
    token: str
    page_size: int = 100
    timeout: int = 30
    verify_ssl: bool = True
