import time

import pyotp
import pytest
from fastapi.testclient import TestClient

from nox.api import contas
from nox.api.app import app
from nox.application.autenticacao import ServicoAutenticacao
from nox.application.perfil import ServicoPerfil
from nox.application.sinais import ATIVOS
from nox.infrastructure.contas_repo import ContasMemoria
from nox.infrastructure.email import EmailMemoria
from nox.infrastructure.seguranca import Cifra, Senhas

SENHA = "lua-cheia-sobre-o-mar"


@pytest.fixture
def cliente():
    repo, cifra = ContasMemoria(), Cifra(Cifra.nova_chave())
    servico = ServicoAutenticacao(repo, cifra, EmailMemoria(),
                                  senhas=Senhas(time_cost=1, memory_cost=1024, parallelism=1))
    perfil = ServicoPerfil(repo, cifra, ATIVOS)
    app.dependency_overrides[contas.servico] = lambda: servico
    app.dependency_overrides[contas.servico_perfil] = lambda: perfil
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


def test_preferencias_lista_e_meus_dados(cliente):
    c, _ = cliente
    assert c.get("/api/conta/preferencias").status_code == 401
    c.post("/api/conta/cadastro", json={"nome": "Ana", "email": "ana@exemplo.com", "senha": SENHA})
    sem_conectar = c.put("/api/conta/preferencias", json={"perfil_risco": "moderado", "frequencia": "cada_sinal",
                                                          "canais": {"push": {"ativo": True}}})
    assert sem_conectar.status_code == 400
    inscricao = {"endpoint": "https://push.exemplo/abc", "keys": {"p256dh": "p", "auth": "a"}}
    assert c.post("/api/conta/push", json=inscricao).status_code == 204
    r = c.put("/api/conta/preferencias", json={"perfil_risco": "moderado", "frequencia": "cada_sinal",
                                                "canais": {"push": {"ativo": True}}})
    assert r.status_code == 200 and r.json()["perfil_risco"] == "moderado"
    assert c.put("/api/conta/lista", json={"ativos": ["XYZUSDT"]}).status_code == 400
    assert c.put("/api/conta/lista", json={"ativos": ["ETHUSDT", "BTCUSDT"]}).json() == {"ativos": ["ETHUSDT", "BTCUSDT"]}
    assert c.get("/api/conta/lista").json()["ativos"] == ["ETHUSDT", "BTCUSDT"]
    dados = c.get("/api/conta/meus-dados")
    assert "attachment" in dados.headers["content-disposition"]
    assert dados.json()["perfil_de_risco"] == "moderado"


def test_lista_de_ativos_publica(cliente):
    c, _ = cliente
    simbolos = [a["simbolo"] for a in c.get("/api/ativos").json()]
    assert "BTCUSDT" in simbolos and len(simbolos) == len(ATIVOS)


def test_config_de_alertas_e_telegram_sem_bot(cliente, monkeypatch):
    c, _ = cliente
    monkeypatch.setenv("NOX_VAPID_PRIVADA", "privada")
    monkeypatch.setenv("NOX_VAPID_PUBLICA", "publica")
    monkeypatch.delenv("NOX_TELEGRAM_TOKEN", raising=False)
    assert c.get("/api/alertas/config").json() == {"push_chave_publica": "publica", "telegram_bot": None}
    c.post("/api/conta/cadastro", json={"nome": "Ana", "email": "ana@exemplo.com", "senha": SENHA})
    r = c.post("/api/conta/telegram")
    assert r.status_code == 503 and "ainda não foi configurado" in r.json()["detail"]


def test_link_do_telegram_com_bot_configurado(cliente, monkeypatch):
    c, _ = cliente
    monkeypatch.setenv("NOX_TELEGRAM_TOKEN", "123:abc")
    monkeypatch.setenv("NOX_TELEGRAM_BOT", "@NoxAlertasBot")
    c.post("/api/conta/cadastro", json={"nome": "Ana", "email": "ana@exemplo.com", "senha": SENHA})
    link = c.post("/api/conta/telegram").json()["link"]
    assert link.startswith("https://t.me/NoxAlertasBot?start=") and len(link.split("=")[1]) >= 32
