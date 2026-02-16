from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AUTO PATCH"
    api_prefix: str = "/api"
    database_url: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_exp_minutes: int = 60 * 24
    admin_email: str | None = None
    admin_password: str | None = None
    agent_bootstrap_token: str | None = None
    frontend_origin: str | None = None
    api_base_url: str | None = None
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None
    agent_rate_limit_seconds: int = 5

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
