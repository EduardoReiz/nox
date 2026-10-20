"""O mesmo contrato do repositório, agora no PostgreSQL. É pulado quando o
banco não está no ar (docker compose up -d postgres)."""

import uuid
from datetime import UTC, datetime, timedelta

import psycopg
import pytest

from nox.domain.contas import ErroDeConta, Usuario
from nox.infrastructure import config
from nox.infrastructure.contas_repo import ContasPostgres


@pytest.fixture
def repo():
    try:
        r = ContasPostgres(config.postgres_dsn())
    except (KeyError, psycopg.OperationalError):
        pytest.skip("PostgreSQL fora do ar")
    yield r
    r.con.execute("DELETE FROM usuario WHERE email LIKE '%@teste.nox'")
    r.con.close()


def novo(email=None) -> Usuario:
    return Usuario(email=email or f"{uuid.uuid4().hex[:8]}@teste.nox", nome="Teste",
                   senha_hash="$argon2id$falso", criado_em=datetime.now(UTC))


def test_usuario_ida_e_volta(repo):
    u = novo()
    repo.criar_usuario(u)
    lido = repo.usuario_por_email(u.email)
    assert lido.id == u.id and lido.nome == "Teste"
    lido.totp_ativo, lido.totp_ultimo_passo = True, 123
    repo.atualizar_usuario(lido)
    assert repo.usuario_por_id(u.id).totp_ultimo_passo == 123
    with pytest.raises(ErroDeConta):
        repo.criar_usuario(novo(u.email))


def test_sessao_desafio_auditoria_e_exclusao(repo):
    u = novo()
    repo.criar_usuario(u)
    agora = datetime.now(UTC)
    repo.criar_sessao("h-sessao-" + u.id, u.id, agora + timedelta(hours=1))
    assert repo.usuario_da_sessao("h-sessao-" + u.id, agora) == u.id
    assert repo.usuario_da_sessao("h-sessao-" + u.id, agora + timedelta(hours=2)) is None

    repo.criar_desafio("2fa", "h-des-" + u.id, u.id, agora + timedelta(minutes=5))
    assert repo.usuario_do_desafio("2fa", "h-des-" + u.id, agora) == u.id
    assert repo.usuario_do_desafio("recuperacao", "h-des-" + u.id, agora) is None
    assert repo.falhar_desafio("h-des-" + u.id) == 1

    repo.registrar("login_falhou", u.id, agora)
    assert repo.contar_eventos(u.id, "login_falhou", agora - timedelta(minutes=1)) == 1

    repo.apagar_usuario(u.id)
    assert repo.usuario_da_sessao("h-sessao-" + u.id, agora) is None
    anonimos = repo.con.execute(
        "SELECT count(*) AS n FROM auditoria WHERE usuario_id IS NULL AND quando = %s", (agora,)).fetchone()
    assert anonimos["n"] >= 1


def test_ativos_lista_e_preferencias(repo):
    u = novo()
    repo.criar_usuario(u)
    repo.garantir_ativos({"BTCUSDT": "Bitcoin", "ETHUSDT": "Ethereum"})
    assert {"BTCUSDT", "ETHUSDT"} <= set(repo.ativos())
    t0 = datetime.now(UTC)
    repo.salvar_lista(u.id, ["BTCUSDT", "ETHUSDT"], t0)
    repo.salvar_lista(u.id, ["ETHUSDT"], t0 + timedelta(days=1))
    assert repo.lista(u.id) == [("ETHUSDT", t0)]
    repo.salvar_preferencia(u.id, "telegram", True, "cifrado")
    repo.salvar_preferencia(u.id, "telegram", False, None)
    assert repo.preferencias(u.id) == [("telegram", False, None)]
    assert repo.seguidores("ETHUSDT") == [u.id]
    repo.criar_desafio("telegram", "h-tg-" + u.id, u.id, t0 + timedelta(days=9999))
    assert repo.usuario_do_desafio("telegram", "h-tg-" + u.id, t0) == u.id
    u.frequencia_alerta = "resumo_diario"
    repo.atualizar_usuario(u)
    assert repo.usuario_por_id(u.id).frequencia_alerta == "resumo_diario"


def test_sinais_e_alertas_no_postgres(repo):
    from nox.infrastructure.sinais_repo import SinaisPostgres
    s = SinaisPostgres(config.postgres_dsn())
    u = novo()
    repo.criar_usuario(u)
    repo.garantir_ativos({"BTCUSDT": "Bitcoin"})
    vela = datetime(2001, 1, 1, tzinfo=UTC) + timedelta(hours=int(uuid.uuid4().int % 100000))
    dados = {"ativo": "BTCUSDT", "gerado_em": datetime.now(UTC).isoformat(), "acao": "comprar", "score": 70,
             "direcao": "alta", "componentes": [{"nome": "tecnico"}], "divergencia": None, "explicacao": "teste"}
    sid = s.salvar(dados, vela)
    assert sid and s.salvar(dados, vela) is None
    s.registrar_alerta(u.id, sid, "resumo", "pendente", datetime.now(UTC))
    assert s.pendentes_resumo()[u.id][0]["explicacao"] == "teste"
    s.marcar_resumo_enviado(u.id, datetime.now(UTC))
    assert u.id not in s.pendentes_resumo()
    s.con.execute("DELETE FROM alerta WHERE usuario_id = %s", (u.id,))
    s.con.execute("DELETE FROM sinal WHERE id = %s", (sid,))
    s.con.close()
