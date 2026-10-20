from datetime import UTC, datetime, timedelta

import pytest

from nox.application.perfil import ServicoPerfil
from nox.domain.contas import ErroDeConta, Usuario
from nox.infrastructure.contas_repo import ContasMemoria
from nox.infrastructure.seguranca import Cifra

ATIVOS = {"BTCUSDT": "Bitcoin", "ETHUSDT": "Ethereum", "SOLUSDT": "Solana"}
INSCRICAO = {"endpoint": "https://fcm.googleapis.com/fcm/send/abc123",
             "keys": {"p256dh": "chave-publica-do-navegador", "auth": "segredo-de-autenticacao"}}


class Relogio:
    def __init__(self):
        self.t = datetime(2026, 10, 20, 12, 0, tzinfo=UTC)

    def __call__(self):
        return self.t


@pytest.fixture
def ctx():
    repo, relogio = ContasMemoria(), Relogio()
    u = Usuario(email="ana@exemplo.com", nome="Ana", senha_hash="x", criado_em=relogio())
    repo.criar_usuario(u)
    return ServicoPerfil(repo, Cifra(Cifra.nova_chave()), ATIVOS, agora=relogio), repo, u, relogio


def test_preferencias_padrao(ctx):
    p, _, u, _ = ctx
    assert p.preferencias(u) == {
        "perfil_risco": None, "frequencia": "cada_sinal",
        "canais": {"push": {"ativo": False, "conectado": False}, "telegram": {"ativo": False, "conectado": False}}}


def test_perfil_fica_cifrado(ctx):
    p, repo, u, _ = ctx
    r = p.salvar_preferencias(u, "moderado", "resumo_diario", {})
    assert r["perfil_risco"] == "moderado" and r["frequencia"] == "resumo_diario"
    assert "moderado" not in repo.usuario_por_id(u.id).perfil_risco_cifrado


@pytest.mark.parametrize("perfil,freq,canais", [
    ("ousado", "cada_sinal", {}),
    ("moderado", "toda_hora", {}),
    ("moderado", "cada_sinal", {"email": {"ativo": True}}),
])
def test_preferencias_invalidas(ctx, perfil, freq, canais):
    p, _, u, _ = ctx
    with pytest.raises(ErroDeConta):
        p.salvar_preferencias(u, perfil, freq, canais)


@pytest.mark.parametrize("canal", ["push", "telegram"])
def test_canal_so_liga_depois_de_conectado(ctx, canal):
    p, _, u, _ = ctx
    with pytest.raises(ErroDeConta, match="Conecte"):
        p.salvar_preferencias(u, None, "cada_sinal", {canal: {"ativo": True}})


def test_push_conectado_fica_cifrado_e_pode_ser_desligado(ctx):
    p, repo, u, _ = ctx
    p.conectar_push(u, INSCRICAO)
    assert p.preferencias(u)["canais"]["push"] == {"ativo": True, "conectado": True}
    assert all("abc123" not in (i or "") for _, _, i in repo.preferencias(u.id))
    assert "abc123" in p.destino(u.id, "push")
    # Desligar mantém a inscrição; religar não precisa pedir permissão de novo.
    p.salvar_preferencias(u, None, "cada_sinal", {"push": {"ativo": False}})
    assert p.destino(u.id, "push") is None
    p.salvar_preferencias(u, None, "cada_sinal", {"push": {"ativo": True}})
    assert p.destino(u.id, "push")


@pytest.mark.parametrize("inscricao", [
    {"endpoint": "http://inseguro.com/x", "keys": {"p256dh": "a", "auth": "b"}},
    {"endpoint": "https://ok.com/x", "keys": {"p256dh": "a"}},
    {},
])
def test_inscricao_push_invalida(ctx, inscricao):
    p, _, u, _ = ctx
    with pytest.raises(ErroDeConta):
        p.conectar_push(u, inscricao)


def test_vinculo_do_telegram_vale_uma_vez_e_expira(ctx):
    p, _, u, relogio = ctx
    codigo = p.iniciar_vinculo_telegram(u)
    assert p.vincular_telegram(codigo, "987654").id == u.id
    assert p.destino(u.id, "telegram") == "987654"
    assert p.vincular_telegram(codigo, "111") is None  # já usado
    novo = p.iniciar_vinculo_telegram(u)
    relogio.t += timedelta(minutes=16)
    assert p.vincular_telegram(novo, "222") is None  # expirado
    assert p.destino(u.id, "telegram") == "987654"


def test_lista_mantem_data_de_quem_continua(ctx):
    p, repo, u, relogio = ctx
    assert p.salvar_lista(u, ["btcusdt", "ETHUSDT", "BTCUSDT"]) == ["BTCUSDT", "ETHUSDT"]
    primeira = dict(repo.lista(u.id))["BTCUSDT"]
    relogio.t += timedelta(days=1)
    assert p.salvar_lista(u, ["BTCUSDT", "SOLUSDT"]) == ["BTCUSDT", "SOLUSDT"]
    assert dict(repo.lista(u.id))["BTCUSDT"] == primeira


def test_lista_recusa_ativo_que_o_nox_nao_acompanha(ctx):
    p, _, u, _ = ctx
    with pytest.raises(ErroDeConta, match="DOGEUSDT"):
        p.salvar_lista(u, ["BTCUSDT", "DOGEUSDT"])


def test_meus_dados_traz_o_essencial_e_nada_tecnico(ctx):
    p, _, u, _ = ctx
    p.conectar_push(u, INSCRICAO)
    p.vincular_telegram(p.iniciar_vinculo_telegram(u), "987654")
    p.salvar_preferencias(u, "conservador", "cada_sinal", {"push": {"ativo": True}, "telegram": {"ativo": True}})
    p.salvar_lista(u, ["SOLUSDT"])
    dados = p.meus_dados(u)
    assert dados["perfil_de_risco"] == "conservador"
    assert dados["alertas"]["canais"]["telegram"]["chat"] == "987654"
    assert dados["ativos_acompanhados"][0]["ativo"] == "SOLUSDT"
    texto = str(dados)
    assert "senha" not in texto and "totp" not in texto and "p256dh" not in texto


def test_excluir_conta_apaga_preferencias_e_lista(ctx):
    p, repo, u, _ = ctx
    p.conectar_push(u, INSCRICAO)
    p.salvar_lista(u, ["BTCUSDT"])
    repo.apagar_usuario(u.id)
    assert repo.preferencias(u.id) == [] and repo.lista(u.id) == []
