from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "scheduler_ai"
    app_env: str = "development"
    database_url: str = "sqlite:///./scheduler.db"

    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db_name: str = "scheduler"

    lmstudio_api_url: str = "http://127.0.0.1:1234"
    lmstudio_api_key: str = "lm-studio"
    lmstudio_model_name: str = "local-model"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
