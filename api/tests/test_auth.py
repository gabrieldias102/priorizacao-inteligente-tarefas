from tests.conftest import registrar


def test_registrar_devolve_token_e_usuario(cliente):
    resposta = cliente.post(
        "/auth/registrar", json={"nome": "Ana", "email": "Ana@Exemplo.com", "senha": "senha-segura"}
    )
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["token_type"] == "bearer"
    assert corpo["usuario"]["email"] == "ana@exemplo.com"
    assert "senha" not in str(corpo)


def test_email_repetido_e_recusado(cliente):
    registrar(cliente)
    resposta = cliente.post(
        "/auth/registrar",
        json={"nome": "Outra", "email": "ANA@exemplo.com", "senha": "outra-senha"},
    )
    assert resposta.status_code == 409


def test_senha_curta_e_recusada(cliente):
    resposta = cliente.post(
        "/auth/registrar", json={"nome": "Ana", "email": "ana@exemplo.com", "senha": "123"}
    )
    assert resposta.status_code == 422


def test_entrar_com_senha_certa_e_errada(cliente):
    registrar(cliente)
    ok = cliente.post(
        "/auth/entrar", data={"username": "ana@exemplo.com", "password": "senha-segura"}
    )
    assert ok.status_code == 200
    assert (
        cliente.get(
            "/auth/eu", headers={"Authorization": f"Bearer {ok.json()['access_token']}"}
        ).json()["nome"]
        == "Ana"
    )

    errada = cliente.post(
        "/auth/entrar", data={"username": "ana@exemplo.com", "password": "errada!!"}
    )
    assert errada.status_code == 401


def test_rotas_protegidas_exigem_token_valido(cliente):
    assert cliente.get("/auth/eu").status_code == 401
    assert cliente.get("/tarefas", headers={"Authorization": "Bearer invalido"}).status_code == 401
