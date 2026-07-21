"""Configuración de la aplicación cargada desde variables de entorno (.env)."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Aplicación
    app_name: str = "MathScribe API"
    environment: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"
    # Se declara como cadena separada por comas (no como lista) porque las
    # plataformas de despliegue sólo inyectan texto plano en las variables de
    # entorno. `cors_origins_list` entrega la lista ya normalizada.
    cors_origins: str = "http://localhost:5173"

    # Base de datos
    database_url: str = "postgresql+psycopg://mathscribe:mathscribe@localhost:5432/mathscribe"

    # Autenticación
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Capa de inteligencia
    recognition_provider: str = "gemini"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.5-flash"
    # Tokens que el modelo puede gastar razonando antes de responder. En los
    # modelos 3.x el razonamiento se factura, y transcribir una expresión no lo
    # necesita. `None` deja el valor por defecto del modelo; 0 lo desactiva.
    gemini_thinking_budget: int | None = None
    # Tarifas por cada 1000 tokens (gemini-3.5-flash: 1,50 USD y 9,00 USD por
    # millón). Se separan porque la salida cuesta seis veces más que la entrada,
    # y los tokens de razonamiento se facturan como salida.
    gemini_input_cost_per_1k: float = 0.0015
    gemini_output_cost_per_1k: float = 0.009
    openai_api_key: str | None = None
    mathpix_app_id: str | None = None
    mathpix_app_key: str | None = None

    # Almacenamiento de objetos (S3)
    s3_endpoint: str | None = None
    s3_bucket: str = "mathscribe-uploads"
    s3_access_key: str | None = None
    s3_secret_key: str | None = None
    s3_region: str = "us-east-1"

    @property
    def cors_origins_list(self) -> list[str]:
        """Orígenes permitidos para CORS, a partir de la cadena separada por comas."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def sqlalchemy_database_url(self) -> str:
        """URL de base de datos con el driver explícito que espera SQLAlchemy.

        Los proveedores administrados (Render, Heroku) entregan la cadena con el
        esquema `postgresql://` o `postgres://`; SQLAlchemy necesita que se
        indique el driver `psycopg` para no recurrir al obsoleto psycopg2.
        """
        url = self.database_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        return url


settings = Settings()
