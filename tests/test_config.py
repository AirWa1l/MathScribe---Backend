"""Pruebas de la normalización de configuración para entornos de despliegue.

Las plataformas administradas (Render) inyectan las variables como texto plano y
entregan la cadena de conexión con un esquema que SQLAlchemy no acepta tal cual.
Estas pruebas fijan ese contrato para que un despliegue no falle en arranque.
"""

from app.core.config import Settings


def test_cors_origins_admite_varios_origenes_separados_por_coma() -> None:
    settings = Settings(cors_origins="https://mathscribe-web.onrender.com, http://localhost:5173")
    assert settings.cors_origins_list == [
        "https://mathscribe-web.onrender.com",
        "http://localhost:5173",
    ]


def test_cors_origins_ignora_entradas_vacias() -> None:
    settings = Settings(cors_origins="https://uno.com,,  ,https://dos.com")
    assert settings.cors_origins_list == ["https://uno.com", "https://dos.com"]


def test_database_url_recibe_el_driver_psycopg() -> None:
    settings = Settings(database_url="postgresql://usuario:clave@host:5432/basedatos")
    assert settings.sqlalchemy_database_url.startswith("postgresql+psycopg://")


def test_database_url_con_esquema_corto_se_normaliza() -> None:
    settings = Settings(database_url="postgres://usuario:clave@host:5432/basedatos")
    assert settings.sqlalchemy_database_url == (
        "postgresql+psycopg://usuario:clave@host:5432/basedatos"
    )


def test_database_url_ya_normalizada_no_se_altera() -> None:
    url = "postgresql+psycopg://usuario:clave@host:5432/basedatos"
    assert Settings(database_url=url).sqlalchemy_database_url == url
