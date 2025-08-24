from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./sg.db"
    secret_key: str = "changeme"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    env: str = "local"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()
