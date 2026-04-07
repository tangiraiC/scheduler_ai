from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Scheduler AI"
    environment: str = Field("development", env="APP_ENV")
    database_url: str = Field("sqlite:///./scheduler.db", env="DATABASE_URL")
    lmstudio_api_url: AnyHttpUrl = Field("http://localhost:8080", env="LMSTUDIO_API_URL")
    lmstudio_api_key: str = Field("changeme", env="LMSTUDIO_API_KEY")
    log_level: str = Field("INFO", env="LOG_LEVEL")

    model_config = SettingsConfigDict(env_file=".env", extra='ignore')


settings = Settings()
