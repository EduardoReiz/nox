"""Velas em tempo real pelo WebSocket da Binance, com reconexão (RNF-004)."""

import asyncio
import json
import logging
from collections.abc import AsyncIterator

import websockets

from nox.domain.mercado import Vela
from nox.infrastructure.binance import FONTE, _de_ms

log = logging.getLogger(__name__)

# A Binance oferece as portas 9443 e 443. A 9443 é a mais citada, mas foi
# bloqueada na rede em que a Experimentação 1 rodou; a 443 é a mesma porta do
# HTTPS e passa por quase qualquer firewall.
URL_WS = "wss://stream.binance.com:443/ws"


def converter_mensagem(msg: dict) -> tuple[Vela, bool]:
    """Mensagem do stream <símbolo>@kline_<intervalo> para (vela, fechada?)."""
    k = msg["k"]
    vela = Vela(
        ativo=k["s"],
        intervalo=k["i"],
        instante=_de_ms(int(k["t"])),
        abertura=float(k["o"]),
        maxima=float(k["h"]),
        minima=float(k["l"]),
        fechamento=float(k["c"]),
        volume=float(k["v"]),
        fonte=FONTE,
    )
    return vela, bool(k["x"])


async def acompanhar(simbolo: str, intervalo: str, espera_max: float = 60.0,
                     url: str = URL_WS) -> AsyncIterator[tuple[Vela, bool, dict]]:
    """Gera (vela, fechada, mensagem bruta) para sempre, reconectando quando cai.

    A espera entre reconexões dobra a cada falha seguida e volta a 1 s quando
    a conexão se firma. A biblioteca responde sozinha aos pings da Binance.
    """
    endereco = f"{url}/{simbolo.lower()}@kline_{intervalo}"
    espera = 1.0
    while True:
        try:
            async with websockets.connect(endereco) as ws:
                log.info("conectado em %s", endereco)
                espera = 1.0
                async for texto in ws:
                    msg = json.loads(texto)
                    vela, fechada = converter_mensagem(msg)
                    yield vela, fechada, msg
        except (OSError, websockets.ConnectionClosed, websockets.InvalidHandshake) as e:
            log.warning("conexão perdida (%s); reconectando em %.0fs", type(e).__name__, espera)
            await asyncio.sleep(espera)
            espera = min(espera * 2, espera_max)
