import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.modelos import Usuario

ALGORITMO = "HS256"
hash_senha = PasswordHash.recommended()
oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/entrar")


def gerar_hash(senha: str) -> str:
    return hash_senha.hash(senha)


def senha_confere(senha: str, hash_salvo: str) -> bool:
    return hash_senha.verify(senha, hash_salvo)


def criar_token(usuario_id: uuid.UUID) -> str:
    expira = datetime.now(UTC) + timedelta(minutes=settings.jwt_expira_minutos)
    return jwt.encode(
        {"sub": str(usuario_id), "exp": expira}, settings.jwt_segredo, algorithm=ALGORITMO
    )


def usuario_atual(
    token: Annotated[str, Depends(oauth2)], db: Annotated[Session, Depends(get_db)]
) -> Usuario:
    nao_autorizado = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Sessão inválida ou expirada",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        dados = jwt.decode(token, settings.jwt_segredo, algorithms=[ALGORITMO])
        usuario_id = uuid.UUID(dados["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise nao_autorizado from None
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise nao_autorizado
    return usuario


UsuarioAtual = Annotated[Usuario, Depends(usuario_atual)]
Db = Annotated[Session, Depends(get_db)]
