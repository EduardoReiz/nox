"""RF-002: o serviço grava no banco as velas fechadas que ainda não estão lá."""

from datetime import UTC, datetime

import httpx

from nox.application.sinais import ATIVOS, ServicoSinais
from nox.infrastructure.binance import ClienteBinance

HORA_MS = 3_600_000
FIM_MS = int(datetime(2026, 10, 20, 12, tzinfo=UTC).timestamp() * 1000)


def rota_com_fim(fim_ms):
    def rota(req: httpx.Request) -> httpx.Response:
        n = int(req.url.params["limit"])
        linhas = []
        for i in range(n):
            abre = fim_ms - (n - i) * HORA_MS
            p = 100 + (i % 9)
            linhas.append([abre, str(p), str(p + 1), str(p - 1), str(p), "10",
                           abre + HORA_MS - 1, "0", 1, "0", "0", "0"])
        return httpx.Response(200, json=linhas)
    return rota


class SeriesFalsas:
    def __init__(self, falhar=False):
        self.velas = {}
        self.gravacoes = []
        self.falhar = falhar

    def ultimas(self, ativo, intervalo, quantidade):
        if self.falhar:
            raise RuntimeError("banco fora do ar")
        guardadas = sorted((v for (a, _, _), v in self.velas.items() if a == ativo), key=lambda v: v.instante)
        return guardadas[-quantidade:]

    def gravar(self, velas):
        self.gravacoes.append(len(velas))
        for v in velas:
            self.velas[(v.ativo, v.intervalo, v.instante)] = v


def servico(series, fim_ms=FIM_MS, agora=datetime(2026, 10, 20, 12, 30, tzinfo=UTC)):
    http = httpx.Client(base_url="https://teste", transport=httpx.MockTransport(rota_com_fim(fim_ms)))
    return ServicoSinais(ClienteBinance(http=http, agora=lambda: agora), agora=lambda: agora, series=series)


def test_primeira_vez_grava_todas_as_velas_de_cada_ativo():
    series = SeriesFalsas()
    servico(series).sinais()
    assert series.gravacoes == [300] * len(ATIVOS)
    assert len({a for a, _, _ in series.velas}) == len(ATIVOS)


def test_nao_regrava_o_que_ja_esta_no_banco_e_acrescenta_a_vela_nova():
    series = SeriesFalsas()
    servico(series).sinais()
    # Uma hora depois fechou mais uma vela: só ela deve ser gravada.
    depois = datetime(2026, 10, 20, 13, 30, tzinfo=UTC)
    servico(series, FIM_MS + HORA_MS, depois).sinais()
    assert series.gravacoes[len(ATIVOS):] == [1] * len(ATIVOS)
    assert len(series.velas) == 301 * len(ATIVOS)


def test_falha_ao_gravar_nao_impede_o_sinal():
    sinais = servico(SeriesFalsas(falhar=True)).sinais()
    assert [s["ativo"] for s in sinais] == list(ATIVOS)


def test_sem_repositorio_continua_funcionando():
    assert len(servico(None).sinais()) == len(ATIVOS)
