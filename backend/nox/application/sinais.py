"""Orquestra a geração dos sinais e converte para o formato que a API entrega.

O formato do sinal (passo 1 da Experimentação 3) está descrito em
docs/contrato_sinal.md. O frontend usa o mesmo formato com dados simulados
e com dados reais, sem mudar os componentes.
"""

import logging
import time
from dataclasses import asdict
from datetime import UTC, datetime

from nox.domain.mercado import Vela
from nox.domain.score import SemSinal, Sinal, gerar_sinal
from nox.infrastructure.binance import ClienteBinance

log = logging.getLogger(__name__)

ATIVOS = {
    "BTCUSDT": "Bitcoin",
    "ETHUSDT": "Ethereum",
    "SOLUSDT": "Solana",
    "BNBUSDT": "BNB",
    "XRPUSDT": "XRP",
    "ADAUSDT": "Cardano",
}
INTERVALO = "1h"
VELAS_POR_CALCULO = 300
CACHE_SEGUNDOS = 60  # o sinal só muda quando fecha uma vela de 1 hora

ROTULOS = {"tecnico": "Análise técnica", "sentimento": "Sentimento do mercado",
           "ml": "Previsão de Machine Learning"}


def _preco(velas: list[Vela]) -> dict:
    ultima = velas[-1]
    dia_antes = velas[-25] if len(velas) >= 25 else velas[0]
    return {
        "ultimo": ultima.fechamento,
        "variacao_24h_pct": round((ultima.fechamento / dia_antes.fechamento - 1) * 100, 2),
        # RNF-006: o horário em que a última vela fechou
        "atualizado_em": (ultima.instante + (velas[-1].instante - velas[-2].instante)).isoformat(),
    }


def para_json(ativo: str, resultado: Sinal | SemSinal, velas: list[Vela]) -> dict:
    base = {"ativo": ativo, "nome": ATIVOS.get(ativo, ativo)}
    if velas:
        base["preco"] = _preco(velas)
    if isinstance(resultado, SemSinal):
        return {**base, "disponivel": False, "motivo": resultado.motivo}
    componentes = []
    for c in resultado.componentes:
        d = asdict(c)
        d["rotulo"] = ROTULOS[c.nome]
        d["forca"] = round(c.forca, 3)
        d["peso"] = round(c.peso, 3)
        d["pontuacao"] = round(c.pontuacao)
        componentes.append(d)
    return {
        **base,
        "disponivel": True,
        "gerado_em": resultado.gerado_em.isoformat(),
        "acao": resultado.acao,
        "score": resultado.score,
        "direcao": resultado.direcao,
        "componentes": componentes,
        "ausentes": [ROTULOS[a] for a in resultado.ausentes],
        "divergencia": resultado.divergencia,
        "explicacao": resultado.explicacao,
        "aviso_risco": resultado.aviso_risco,
    }


class ServicoSinais:
    def __init__(self, cliente: ClienteBinance | None = None, agora=lambda: datetime.now(UTC), series=None):
        self.cliente = cliente or ClienteBinance()
        self.agora = agora
        # Quando há um repositório de séries (RF-002), cada vela fechada nova é gravada.
        self.series = series
        self._cache: tuple[float, list[dict], dict[str, list[Vela]]] | None = None

    def _guardar(self, ativo: str, velas: list[Vela]) -> None:
        """Grava só as velas fechadas que ainda não estão no banco (uma vela
        fechada não muda). Falha ao gravar não impede o cálculo do sinal."""
        if not self.series:
            return
        try:
            gravadas = self.series.ultimas(ativo, INTERVALO, 1)
            desde = gravadas[-1].instante if gravadas else None
            novas = [v for v in velas if desde is None or v.instante > desde]
            if novas:
                self.series.gravar(novas)
        except Exception:
            log.exception("não foi possível gravar as velas de %s", ativo)

    def _atualizar(self):
        sinais, series = [], {}
        agora = self.agora()
        for ativo in ATIVOS:
            velas = self.cliente.velas(ativo, INTERVALO, VELAS_POR_CALCULO)
            self._guardar(ativo, velas)
            series[ativo] = velas
            sinais.append(para_json(ativo, gerar_sinal(ativo, velas, agora), velas))
        self._cache = (time.monotonic(), sinais, series)

    def _dados(self):
        if self._cache is None or time.monotonic() - self._cache[0] > CACHE_SEGUNDOS:
            self._atualizar()
        return self._cache

    def sinais(self) -> list[dict]:
        return self._dados()[1]

    def sinais_com_vela(self) -> list[tuple[dict, datetime]]:
        """Cada sinal com o instante da última vela fechada que o gerou. É a
        chave que impede gravar o mesmo sinal duas vezes (RF-008)."""
        _, sinais, series = self._dados()
        return [(s, series[s["ativo"]][-1].instante) for s in sinais if series.get(s["ativo"])]

    def velas(self, ativo: str, quantidade: int) -> list[dict]:
        series = self._dados()[2]
        if ativo not in series:
            raise KeyError(ativo)
        return [{"instante": v.instante.isoformat(), "fechamento": v.fechamento}
                for v in series[ativo][-quantidade:]]
