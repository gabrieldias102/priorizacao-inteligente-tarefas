import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app


@pytest.fixture
def sessao_fabrica():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    engine.dispose()


@pytest.fixture
def cliente(sessao_fabrica):
    def db_de_teste():
        with sessao_fabrica() as sessao:
            yield sessao

    app.dependency_overrides[get_db] = db_de_teste
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def registrar(cliente, email="ana@exemplo.com", senha="senha-segura"):
    resposta = cliente.post("/auth/registrar", json={"nome": "Ana", "email": email, "senha": senha})
    assert resposta.status_code == 201, resposta.text
    return {"Authorization": f"Bearer {resposta.json()['access_token']}"}


@pytest.fixture
def auth(cliente):
    return registrar(cliente)


TAREFA = {
    "titulo": "Entregar relatório",
    "categoria": "trabalho",
    "impacto": 4,
    "complexidade": 3,
    "esforco_estimado": 2.5,
}
