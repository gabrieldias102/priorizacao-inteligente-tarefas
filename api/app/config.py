from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ml_url: str = "http://localhost:8001"
    database_url: str = "postgresql+psycopg://tarefas:tarefas@localhost:5432/tarefas"
    cors_origins: list[str] = ["http://localhost:5173"]

    # Troque em qualquer ambiente fora da máquina de desenvolvimento.
    jwt_segredo: str = "dev-inseguro-troque-este-segredo"
    jwt_expira_minutos: int = 60 * 24 * 7


settings = Settings()
