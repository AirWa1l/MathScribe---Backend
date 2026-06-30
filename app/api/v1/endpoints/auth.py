"""Endpoints de autenticación: registro e inicio de sesión (PB-09).

Andamiaje: la verificación de credenciales y la emisión real de JWT se implementan
en historias posteriores.
"""

from fastapi import APIRouter, status

from app.schemas.user import TokenResponse, UserCreate, UserLogin, UserRead

router = APIRouter()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate) -> UserRead:
    """Crea una cuenta de usuario."""
    # TODO: hashear contraseña y persistir en PostgreSQL.
    return UserRead(id=1, email=payload.email, name=payload.name)


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin) -> TokenResponse:
    """Autentica al usuario y emite un token de acceso."""
    # TODO: validar credenciales y firmar el JWT con la configuración de la app.
    return TokenResponse(access_token="dummy-token", token_type="bearer")
