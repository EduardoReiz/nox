from datetime import UTC, datetime

import httpx
import pytest
from fastapi.testclient import TestClient

from nox.api import app as modulo_app
from nox.application.sinais import ATIVOS, ServicoSinais
from nox.infrastructure.binance import ClienteBinance

HORA_MS = 3_600_000
AGORA = datetime(2026, 10, 20, 12, 30, tzinfo=UTC)
FIM_MS = int(datetime(2026, 10, 20, 12, tzinfo=UTC).timestamp() * 1000)


def rota(req: httpx.Request) -> httpx.Response:
    n = int(req.url.params["limit"])
    linhas = []
    for i in range(n):
        abre = FIM_MS - (n - i) * HORA_MS
        p = 100 + (i % 9)
        linhas.append([abre, str(p), str(p + 1), str(p - 1), str(p), "10",
                       abre + HORA_MS - 1, "0", 1, "0", "0", "0"])
    return httpx.Response(200, json=linhas)


@pytest.fixture
def cliente(monkeypatch):
    http = httpx.Client(base_url="https://teste", transport=httpx.MockTransport(rota))
    binance = ClienteBinance(http=http, agora=lambda: AGORA)
    monkeypatch.setattr(modulo_app, "servico", ServicoSinais(binance, agora=lambda: AGORA))
    return TestClient(modulo_app.app)


def test_feed_traz_um_sinal_por_ativo_com_explicacao_e_aviso(cliente):
    sinais = cliente.get("/api/sinais").json()
    assert [s["ativo"] for s in sinais] == list(ATIVOS)
    for s in sinais:
        assert s["disponivel"] is True
        assert s["acao"] in {"comprar", "vender", "manter"}
        assert 0 <= s["score"] <= 100
        assert s["explicacao"] and s["aviso_risco"]
        assert s["preco"]["atualizado_em"] == "2026-10-20T12:00:00+00:00"
        assert s["componentes"][0]["rotulo"] == "Análise técnica"


def test_detalhe_e_ativo_desconhecido(cliente):
    assert cliente.get("/api/sinais/btcusdt").json()["ativo"] == "BTCUSDT"
    assert cliente.get("/api/sinais/XYZ").status_code == 404


def test_velas_para_o_grafico(cliente):
    velas = cliente.get("/api/ativos/ETHUSDT/velas?quantidade=24").json()
    assert len(velas) == 24
    assert set(velas[0]) == {"instante", "fechamento"}
