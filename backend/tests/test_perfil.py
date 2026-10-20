from datetime import UTC, datetime, timedelta

import pytest

from nox.application.perfil import ServicoPerfil
from nox.domain.contas import ErroDeConta, Usuario, normalizar_telegram
from nox.infrastructure.contas_repo import ContasMemoria
from nox.infrastructure.seguranca import Cifra

ATIVOS = {"BTCUSDT": "Bitcoin", "ETHUSDT": "Ethereum", "SOLUSDT": "Solana"}


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
    assert p.preferencias(u) == {"perfil_risco": None, "frequencia": "cada_sinal",
                                 "canais": {"push": {"ativo": False}, "telegram": {"ativo": False}}}


def test_perfil_e_telegram_ficam_cifrados(ctx):
    p, repo, u, _ = ctx
    r = p.salvar_preferencias(u, "moderado", "resumo_diario",
                              {"push": {"ativo": True}, "telegram": {"ativo": True, "usuario": "ana_silva"}})
    assert r["perfil_risco"] == "moderado"
    assert r["canais"]["telegram"] == {"ativo": True, "usuario": "@ana_silva"}
    guardado = repo.usuario_por_id(u.id)
    assert "moderado" not in guardado.perfil_risco_cifrado
    assert all("ana_silva" not in (i or "") for _, _, i in repo.preferencias(u.id))
    assert p.preferencias(guardado)["frequencia"] == "resumo_diario"


@pytest.mark.parametrize("perfil,freq,canais", [
    ("ousado", "cada_sinal", {}),
    ("moderado", "toda_hora", {}),
    ("moderado", "cada_sinal", {"email": {"ativo": True}}),
    ("moderado", "cada_sinal", {"telegram": {"ativo": True}}),  # Telegram ligado sem usuário
])
def test_preferencias_invalidas(ctx, perfil, freq, canais):
    p, _, u, _ = ctx
    with pytest.raises(ErroDeConta):
        p.salvar_preferencias(u, perfil, freq, canais)


@pytest.mark.parametrize("entrada,saida", [("@maria_silva", "@maria_silva"), (" joao2026 ", "@joao2026")])
def test_usuario_do_telegram(entrada, saida):
    assert normalizar_telegram(entrada) == saida


@pytest.mark.parametrize("entrada", ["abc", "@1abcde", "maria silva", "a" * 40])
def test_usuario_do_telegram_invalido(entrada):
    with pytest.raises(ErroDeConta):
        normalizar_telegram(entrada)


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


def test_meus_dados_traz_tudo_decifrado_e_nada_de_senha(ctx):
    p, _, u, _ = ctx
    p.salvar_preferencias(u, "conservador", "cada_sinal", {"telegram": {"ativo": True, "usuario": "@ana_silva"}})
    p.salvar_lista(u, ["SOLUSDT"])
    dados = p.meus_dados(u)
    assert dados["perfil_de_risco"] == "conservador"
    assert dados["alertas"]["canais"]["telegram"]["usuario"] == "@ana_silva"
    assert dados["ativos_acompanhados"][0]["ativo"] == "SOLUSDT"
    assert "senha" not in str(dados) and "totp" not in str(dados)


def test_excluir_conta_apaga_preferencias_e_lista(ctx):
    p, repo, u, _ = ctx
    p.salvar_preferencias(u, "arrojado", "cada_sinal", {"push": {"ativo": True}})
    p.salvar_lista(u, ["BTCUSDT"])
    repo.apagar_usuario(u.id)
    assert repo.preferencias(u.id) == [] and repo.lista(u.id) == []
