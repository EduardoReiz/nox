from datetime import UTC, datetime, timedelta

import httpx
import pytest

from nox.infrastructure.binance import ClienteBinance, FalhaColeta, converter_vela

HORA_MS = 3_600_000
T0_MS = 1_790_000_000_000 - 1_790_000_000_000 % HORA_MS


def linha(i: int, preco: float = 100.0) -> list:
    abre = T0_MS + i * HORA_MS
    return [abre, str(preco), str(preco + 2), str(preco - 2), str(preco + 1), "5.5",
            abre + HORA_MS - 1, "550.0", 42, "2.0", "200.0", "0"]


def cliente(rota, agora_ms: int | None = None, **kw) -> ClienteBinance:
    http = httpx.Client(base_url="https://teste", transport=httpx.MockTransport(rota))
    agora = datetime.fromtimestamp((agora_ms or T0_MS + 10_000 * HORA_MS) / 1000, tz=UTC)
    return ClienteBinance(http=http, dormir=lambda s: None, agora=lambda: agora, **kw)


def test_converte_linha_da_binance():
    v = converter_vela("BTCUSDT", "1h", linha(0))
    assert v.instante == datetime.fromtimestamp(T0_MS / 1000, tz=UTC)
    assert (v.abertura, v.maxima, v.minima, v.fechamento, v.volume) == (100, 102, 98, 101, 5.5)
    assert v.fonte == "binance"


@pytest.mark.parametrize("bruta", [[1, "2"], "texto", [None, "1", "2", "0", "1", "1", 9]])
def test_linha_quebrada_gera_erro(bruta):
    with pytest.raises(ValueError):
        converter_vela("BTCUSDT", "1h", bruta)


def test_descarta_linha_quebrada_e_vela_aberta():
    agora = T0_MS + 2 * HORA_MS + 1000  # a vela 2 ainda está aberta
    resposta = [linha(0), [1, "x"], linha(1), linha(2)]
    c = cliente(lambda req: httpx.Response(200, json=resposta), agora_ms=agora)
    velas = c.velas("BTCUSDT", "1h")
    assert len(velas) == 2
    assert len(c.descartadas) == 1


def test_historico_pagina_ate_acabar():
    pedidos = []

    def rota(req):
        inicio = int(req.url.params["startTime"])
        pedidos.append(inicio)
        i0 = (inicio - T0_MS) // HORA_MS
        n = 1000 if len(pedidos) == 1 else 300
        return httpx.Response(200, json=[linha(i0 + i) for i in range(n)])

    c = cliente(rota)
    velas = c.historico("BTCUSDT", "1h", datetime.fromtimestamp(T0_MS / 1000, tz=UTC))
    assert len(velas) == 1300
    assert pedidos[1] == T0_MS + 1000 * HORA_MS
    assert all(b.instante - a.instante == timedelta(hours=1) for a, b in zip(velas, velas[1:]))


def test_respeita_retry_after_no_429():
    esperas, respostas = [], iter([
        httpx.Response(429, headers={"Retry-After": "7"}),
        httpx.Response(200, json=[linha(0)], headers={"x-mbx-used-weight-1m": "12"}),
    ])
    c = cliente(lambda req: next(respostas))
    c.dormir = esperas.append
    assert len(c.velas("BTCUSDT", "1h")) == 1
    assert esperas == [7.0]
    assert c.peso_usado == 12


def test_falha_de_rede_espera_cada_vez_mais_e_desiste():
    esperas = []

    def rota(req):
        raise httpx.ConnectError("sem rede")

    c = cliente(rota, max_tentativas=4, espera_base=0.5)
    c.dormir = esperas.append
    with pytest.raises(FalhaColeta):
        c.velas("BTCUSDT", "1h")
    assert esperas == [0.5, 1.0, 2.0]


def test_erro_do_pedido_nao_repete():
    chamadas = []

    def rota(req):
        chamadas.append(1)
        return httpx.Response(400, json={"code": -1121, "msg": "Invalid symbol."})

    with pytest.raises(FalhaColeta, match="400"):
        cliente(rota).velas("XYZ", "1h")
    assert len(chamadas) == 1
