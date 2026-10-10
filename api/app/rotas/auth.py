from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from app.esquemas import Token, UsuarioCriar, UsuarioSaida
from app.modelos import Usuario
from app.seguranca import Db, UsuarioAtual, criar_token, gerar_hash, senha_confere

rotas = APIRouter(prefix="/auth", tags=["autenticação"])


def token_para(usuario: Usuario) -> Token:
    return Token(access_token=criar_token(usuario.id), usuario=UsuarioSaida.model_validate(usuario))


@rotas.post("/registrar", status_code=status.HTTP_201_CREATED)
def registrar(dados: UsuarioCriar, db: Db) -> Token:
    email = dados.email.lower()
    if db.scalar(select(Usuario).where(Usuario.email == email)) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Já existe uma conta com esse e-mail")
    usuario = Usuario(nome=dados.nome, email=email, senha_hash=gerar_hash(dados.senha))
    db.add(usuario)
    db.commit()
    return token_para(usuario)


@rotas.post("/entrar")
def entrar(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: Db) -> Token:
    """Login no formato OAuth2: o e-mail vai no campo `username`."""
    usuario = db.scalar(select(Usuario).where(Usuario.email == form.username.lower()))
    if usuario is None or not senha_confere(form.password, usuario.senha_hash):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "E-mail ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_para(usuario)


@rotas.get("/eu")
def eu(usuario: UsuarioAtual) -> UsuarioSaida:
    return UsuarioSaida.model_validate(usuario)
