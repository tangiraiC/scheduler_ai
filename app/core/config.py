from pydantic import AnyHttpUrl, BaseSettings, Field


class Settings(BaseSettings):
    app_name: str = "Scheduler AI"
    environment: str = Field("development", env="APP_ENV")
    database_url: str = Field("sqlite:///./scheduler.db", env="DATABASE_URL")
    lmstudio_api_url: AnyHttpUrl = Field("http://localhost:8080", env="LMSTUDIO_API_URL")
    lmstudio_api_key: str = Field("changeme", env="LMSTUDIO_API_KEY")
    log_level: str = Field("INFO", env="LOG_LEVEL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
