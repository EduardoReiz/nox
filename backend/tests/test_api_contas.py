import time

import pyotp
import pytest
from fastapi.testclient import TestClient

from nox.api import contas
from nox.api.app import app
from nox.application.autenticacao import ServicoAutenticacao
from nox.infrastructure.contas_repo import ContasMemoria
from nox.infrastructure.email import EmailMemoria
from nox.infrastructure.seguranca import Cifra, Senhas

SENHA = "lua-cheia-sobre-o-mar"


@pytest.fixture
def cliente():
    servico = ServicoAutenticacao(ContasMemoria(), Cifra(Cifra.nova_chave()), EmailMemoria(),
                                  senhas=Senhas(time_cost=1, memory_cost=1024, parallelism=1))
    app.dependency_overrides[contas.servico] = lambda: servico
    yield TestClient(app), servico
    app.dependency_overrides.clear()


def test_cadastro_abre_sessao_em_cookie_httponly(cliente):
    c, _ = cliente
    r = c.post("/api/conta/cadastro", json={"nome": "Ana", "email": "ana@exemplo.com", "senha": SENHA})
    assert r.status_code == 201
    cookie = r.headers["set-cookie"]
    assert "nox_sessao=" in cookie and "HttpOnly" in cookie and "SameSite=strict" in cookie
    assert set(r.json()) == {"nome", "email", "dois_fatores", "criado_em"}
    assert c.get("/api/conta/eu").json()["email"] == "ana@exemplo.com"


def test_sem_sessao_eu_responde_401(cliente):
    c, _ = cliente
    assert c.get("/api/conta/eu").status_code == 401


def test_erro_de_validacao_volta_com_mensagem(cliente):
    c, _ = cliente
    r = c.post("/api/conta/cadastro", json={"nome": "Ana", "email": "ana@exemplo.com", "senha": "curta"})
    assert r.status_code == 400
    assert "pelo menos 10" in r.json()["detail"]


def test_fluxo_com_2fa_pela_api(cliente):
    c, _ = cliente
    c.post("/api/conta/cadastro", json={"nome": "Ana", "email": "ana@exemplo.com", "senha": SENHA})
    segredo = c.post("/api/conta/2fa/iniciar").json()["segredo"]
    assert c.post("/api/conta/2fa/ativar", json={"codigo": pyotp.TOTP(segredo).now()}).status_code == 200
    c.post("/api/conta/sair")
    assert c.get("/api/conta/eu").status_code == 401

    r = c.post("/api/conta/entrar", json={"email": "ana@exemplo.com", "senha": SENHA}).json()
    assert r["precisa_codigo"] is True and "usuario" not in r
    # Ainda sem sessão: só a senha não basta.
    assert c.get("/api/conta/eu").status_code == 401
    # O mesmo código da ativação não pode ser reaproveitado; usa o do próximo passo.
    codigo = pyotp.TOTP(segredo).at(time.time() + 30)
    ok = c.post("/api/conta/entrar/codigo", json={"desafio": r["desafio"], "codigo": codigo})
    assert ok.status_code == 200
    assert c.get("/api/conta/eu").json()["dois_fatores"] is True


def test_esqueci_responde_igual_para_qualquer_email(cliente):
    c, _ = cliente
    c.post("/api/conta/cadastro", json={"nome": "Ana", "email": "ana@exemplo.com", "senha": SENHA})
    a = c.post("/api/conta/senha/esqueci", json={"email": "ana@exemplo.com"})
    b = c.post("/api/conta/senha/esqueci", json={"email": "ninguem@exemplo.com"})
    assert a.status_code == b.status_code == 202
    assert a.json() == b.json()
