from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Smart Waste Management API"
    environment: str = "development"
    database_url: str = "sqlite:///./waste.db"
    secret_key: str = "CHANGE_ME_TO_A_LONG_RANDOM_SECRET"
    algorithm: str = "HS256"
    access_token_minutes: int = 30
    refresh_token_days: int = 7
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
