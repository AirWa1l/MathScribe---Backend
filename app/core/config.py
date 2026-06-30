"""Configuración de la aplicación cargada desde variables de entorno (.env)."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Aplicación
    app_name: str = "MathScribe API"
    environment: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:5173"]

    # Base de datos
    database_url: str = "postgresql+psycopg://mathscribe:mathscribe@localhost:5432/mathscribe"

    # Autenticación
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Capa de inteligencia
    recognition_provider: str = "gemini"
    gemini_api_key: str | None = None
    openai_api_key: str | None = None
    mathpix_app_id: str | None = None
    mathpix_app_key: str | None = None

    # Almacenamiento de objetos (S3)
    s3_endpoint: str | None = None
    s3_bucket: str = "mathscribe-uploads"
    s3_access_key: str | None = None
    s3_secret_key: str | None = None
    s3_region: str = "us-east-1"


settings = Settings()
