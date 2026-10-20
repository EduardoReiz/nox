"""Coleta de velas pela API REST pública da Binance (RF-001, RNF-004).

Não usa chave de API: os dados de mercado são públicos, e o Nox nunca pede
chave com permissão de negociação (RNE-007).
"""

import logging
import time
from datetime import UTC, datetime

import httpx

from nox.domain.mercado import INTERVALOS, Vela

log = logging.getLogger(__name__)

URL_BASE = "https://api.binance.com"
FONTE = "binance"
LIMITE_POR_PAGINA = 1000  # máximo aceito pelo endpoint /api/v3/klines

# 429: passou do limite de requisições. 418: o IP foi bloqueado por insistir
# depois do 429. Os dois trazem Retry-After. 5xx são falhas do lado deles.
STATUS_REPETIR = {418, 429, 500, 502, 503, 504}


class FalhaColeta(RuntimeError):
    pass


def _ms(instante: datetime) -> int:
    return int(instante.timestamp() * 1000)


def _de_ms(ms: int) -> datetime:
    return datetime.fromtimestamp(ms / 1000, tz=UTC)


def converter_vela(simbolo: str, intervalo: str, bruta: list) -> Vela:
    """Transforma uma linha do /klines no formato interno.

    Formato da Binance: [abertura_ms, abertura, máxima, mínima, fechamento,
    volume, fechamento_ms, volume_cotacao, negócios, ...], com os preços como
    texto para não perder casas decimais.
    """
    if not isinstance(bruta, list) or len(bruta) < 7:
        raise ValueError(f"vela incompleta: {bruta!r}")
    try:
        return Vela(
            ativo=simbolo,
            intervalo=intervalo,
            instante=_de_ms(int(bruta[0])),
            abertura=float(bruta[1]),
            maxima=float(bruta[2]),
            minima=float(bruta[3]),
            fechamento=float(bruta[4]),
            volume=float(bruta[5]),
            fonte=FONTE,
        )
    except (TypeError, ValueError) as e:
        raise ValueError(f"vela com valor inválido: {bruta!r}") from e


class ClienteBinance:
    def __init__(
        self,
        http: httpx.Client | None = None,
        max_tentativas: int = 5,
        espera_base: float = 1.0,
        dormir=time.sleep,
        agora=lambda: datetime.now(UTC),
    ):
        self.http = http or httpx.Client(base_url=URL_BASE, timeout=10)
        self.max_tentativas = max_tentativas
        self.espera_base = espera_base
        self.dormir = dormir
        self.agora = agora
        self.peso_usado: int | None = None  # peso consumido no minuto, informado pela Binance
        self.descartadas: list[str] = []

    def _get(self, caminho: str, params: dict):
        for tentativa in range(1, self.max_tentativas + 1):
            try:
                resp = self.http.get(caminho, params=params)
            except httpx.TransportError as e:
                espera = self.espera_base * 2 ** (tentativa - 1)
                log.warning("tentativa %d: falha de rede (%s); nova tentativa em %.1fs",
                            tentativa, type(e).__name__, espera)
            else:
                peso = resp.headers.get("x-mbx-used-weight-1m")
                if peso is not None:
                    self.peso_usado = int(peso)
                if resp.status_code == 200:
                    return resp.json()
                if resp.status_code not in STATUS_REPETIR:
                    raise FalhaColeta(f"HTTP {resp.status_code}: {resp.text[:200]}")
                retry_after = resp.headers.get("retry-after")
                espera = (float(retry_after) if retry_after
                          else self.espera_base * 2 ** (tentativa - 1))
                log.warning("tentativa %d: HTTP %d; nova tentativa em %.1fs",
                            tentativa, resp.status_code, espera)

            if tentativa == self.max_tentativas:
                break
            self.dormir(espera)

        raise FalhaColeta(f"{caminho} falhou depois de {self.max_tentativas} tentativas")

    def velas_brutas(self, simbolo: str, intervalo: str, inicio: datetime | None = None,
                     fim: datetime | None = None, limite: int = LIMITE_POR_PAGINA) -> list:
        params = {"symbol": simbolo, "interval": intervalo, "limit": limite}
        if inicio:
            params["startTime"] = _ms(inicio)
        if fim:
            params["endTime"] = _ms(fim)
        return self._get("/api/v3/klines", params)

    def _converter_fechadas(self, simbolo: str, intervalo: str, brutas: list) -> list[Vela]:
        """Converte e descarta o que não serve: linhas quebradas e a vela que
        ainda está aberta (a última da resposta muda até o intervalo acabar)."""
        agora_ms = _ms(self.agora())
        velas = []
        for b in brutas:
            try:
                vela = converter_vela(simbolo, intervalo, b)
            except ValueError as e:
                self.descartadas.append(str(e))
                continue
            if int(b[6]) >= agora_ms:
                continue
            velas.append(vela)
        return velas

    def velas(self, simbolo: str, intervalo: str, quantidade: int = 500) -> list[Vela]:
        """As últimas `quantidade` velas fechadas (até 1000)."""
        brutas = self.velas_brutas(simbolo, intervalo, limite=min(quantidade + 1, LIMITE_POR_PAGINA))
        return self._converter_fechadas(simbolo, intervalo, brutas)[-quantidade:]

    def historico(self, simbolo: str, intervalo: str, inicio: datetime,
                  fim: datetime | None = None) -> list[Vela]:
        """Histórico longo, pedido em páginas de 1000 velas."""
        passo = INTERVALOS[intervalo]
        velas: list[Vela] = []
        cursor = inicio
        while True:
            brutas = self.velas_brutas(simbolo, intervalo, inicio=cursor, fim=fim)
            pagina = self._converter_fechadas(simbolo, intervalo, brutas)
            velas.extend(pagina)
            if len(brutas) < LIMITE_POR_PAGINA or not pagina:
                break
            cursor = pagina[-1].instante + passo
        return velas
