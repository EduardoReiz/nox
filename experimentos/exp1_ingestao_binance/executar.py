"""Experimentação 1 – Ingestão de dados de mercado da Binance em Python.

Segue os seis passos do procedimento da seção 19.2 e grava tudo em
evidencias/. Rodar a partir da pasta backend, com o ambiente ativado:

    python ../experimentos/exp1_ingestao_binance/executar.py [segundos_de_websocket]
"""

import asyncio
import csv
import json
import logging
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx

from nox.domain.mercado import validar_serie
from nox.infrastructure.binance import URL_BASE, ClienteBinance, FalhaColeta
from nox.infrastructure.binance_ws import acompanhar

PASTA = Path(__file__).parent / "evidencias"
ATIVOS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
INTERVALO = "1h"

log = logging.getLogger("exp1")


def configurar_log():
    PASTA.mkdir(exist_ok=True)
    formato = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    for destino in (logging.FileHandler(PASTA / "execucao.log", mode="w", encoding="utf-8"),
                    logging.StreamHandler()):
        destino.setFormatter(formato)
        logging.getLogger().addHandler(destino)
    logging.getLogger().setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def salvar_csv(caminho: Path, velas):
    with caminho.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ativo", "intervalo", "instante", "abertura", "maxima", "minima",
                    "fechamento", "volume", "fonte"])
        for v in velas:
            w.writerow([v.ativo, v.intervalo, v.instante.isoformat(), v.abertura, v.maxima,
                        v.minima, v.fechamento, v.volume, v.fonte])


def passo_1_a_4(cliente: ClienteBinance) -> dict:
    resumo = {}
    for ativo in ATIVOS:
        # Passo 2: guarda a resposta crua (início e fim) para registrar o formato real.
        brutas = cliente.velas_brutas(ativo, INTERVALO, limite=1000)
        (PASTA / f"resposta_bruta_{ativo}.json").write_text(
            json.dumps({"coletado_em": datetime.now(UTC).isoformat(),
                        "endpoint": f"{URL_BASE}/api/v3/klines?symbol={ativo}&interval={INTERVALO}&limit=1000",
                        "linhas_recebidas": len(brutas),
                        "primeiras": brutas[:3], "ultimas": brutas[-2:]}, indent=2),
            encoding="utf-8")

        # Passos 1 e 3: velas fechadas no formato interno.
        inicio = time.perf_counter()
        velas = cliente.velas(ativo, INTERVALO, quantidade=1000)
        ms = (time.perf_counter() - inicio) * 1000
        salvar_csv(PASTA / f"velas_{ativo}_{INTERVALO}.csv", velas)

        # Passo 4: campos inválidos, duplicadas, ordem e lacunas.
        rel = validar_serie(velas)
        resumo[ativo] = {
            "linhas_recebidas": len(brutas),
            "velas_fechadas": len(velas),
            "descartada_vela_aberta": len(brutas) - len(velas),
            "primeira": velas[0].instante.isoformat(),
            "ultima": velas[-1].instante.isoformat(),
            "tempo_requisicao_ms": round(ms),
            "invalidas": len(rel.invalidas),
            "duplicadas": len(rel.duplicadas),
            "fora_de_ordem": len(rel.fora_de_ordem),
            "lacunas": [[a.isoformat(), b.isoformat()] for a, b in rel.lacunas],
            "peso_usado_no_minuto": cliente.peso_usado,
        }
        log.info("%s: %d velas fechadas, íntegra=%s", ativo, len(velas), rel.integra)

    # Histórico longo: precisa de várias páginas de 1000.
    inicio = datetime(2026, 1, 1, tzinfo=UTC)
    t = time.perf_counter()
    historico = cliente.historico("BTCUSDT", INTERVALO, inicio)
    rel = validar_serie(historico)
    resumo["historico_paginado_BTCUSDT"] = {
        "desde": inicio.isoformat(),
        "velas": len(historico),
        "paginas": -(-len(historico) // 1000),
        "tempo_total_s": round(time.perf_counter() - t, 2),
        "lacunas": [[a.isoformat(), b.isoformat()] for a, b in rel.lacunas],
        "duplicadas": len(rel.duplicadas),
        "peso_usado_no_minuto": cliente.peso_usado,
    }
    log.info("histórico BTCUSDT desde %s: %d velas, %d lacunas",
             inicio.date(), len(historico), len(rel.lacunas))
    return resumo


async def passo_5(segundos: int) -> dict:
    """WebSocket de velas de 1 minuto do BTC por alguns minutos."""
    mensagens, fechadas = 0, []
    arquivo = (PASTA / "websocket_BTCUSDT_1m.jsonl").open("w", encoding="utf-8")
    fim = time.monotonic() + segundos

    async def ler():
        nonlocal mensagens
        async for vela, fechada, bruta in acompanhar("BTCUSDT", "1m"):
            mensagens += 1
            arquivo.write(json.dumps(bruta) + "\n")
            if fechada:
                fechadas.append(vela.instante.isoformat())
                log.info("websocket: vela de %s fechou em %.2f", vela.instante.time(), vela.fechamento)
            if time.monotonic() > fim:
                return

    try:
        await asyncio.wait_for(ler(), timeout=segundos + 30)
    except TimeoutError:
        log.error("websocket: nenhuma conexão firmou em %ds", segundos + 30)
    finally:
        arquivo.close()
    return {"segundos": segundos, "mensagens": mensagens,
            "mensagens_por_segundo": round(mensagens / segundos, 2), "velas_fechadas": fechadas}


async def reconexao_simulada(segundos: int = 10) -> dict:
    """Aponta para uma porta que não responde e registra as esperas crescentes."""
    tentativas = []

    class Coletor(logging.Handler):
        def emit(self, registro):
            tentativas.append(registro.getMessage())

    origem = logging.getLogger("nox.infrastructure.binance_ws")
    coletor = Coletor()
    origem.addHandler(coletor)
    try:
        await asyncio.wait_for(
            anext(acompanhar("BTCUSDT", "1m", url="ws://127.0.0.1:9/ws")), timeout=segundos)
    except TimeoutError:
        pass
    finally:
        origem.removeHandler(coletor)
    return {"duracao_s": segundos, "mensagens_de_reconexao": tentativas}


def passo_6() -> dict:
    resultado = {}

    # Queda de rede: endereço que recusa conexão.
    sem_rede = ClienteBinance(http=httpx.Client(base_url="http://127.0.0.1:9", timeout=2),
                              max_tentativas=4, espera_base=0.5)
    t = time.perf_counter()
    try:
        sem_rede.velas("BTCUSDT", INTERVALO)
    except FalhaColeta as e:
        resultado["queda_de_rede"] = {"erro_final": str(e),
                                      "tempo_ate_desistir_s": round(time.perf_counter() - t, 2)}

    # Limite de requisições: não dá para forçar um 429 real sem abusar da API,
    # então as duas primeiras respostas são simuladas e a terceira é a Binance de verdade.
    real = httpx.HTTPTransport()
    contador = {"n": 0}

    def transporte(req):
        contador["n"] += 1
        if contador["n"] <= 2:
            return httpx.Response(429, headers={"Retry-After": "1"}, request=req)
        return real.handle_request(req)

    limitado = ClienteBinance(http=httpx.Client(base_url=URL_BASE, timeout=10,
                                                transport=httpx.MockTransport(transporte)))
    t = time.perf_counter()
    velas = limitado.velas("BTCUSDT", INTERVALO, quantidade=10)
    resultado["limite_de_requisicoes"] = {
        "respostas_429_simuladas": 2, "retry_after_s": 1, "requisicoes": contador["n"],
        "velas_obtidas_no_fim": len(velas), "tempo_total_s": round(time.perf_counter() - t, 2)}
    return resultado


def main():
    segundos_ws = int(sys.argv[1]) if len(sys.argv) > 1 else 180
    configurar_log()
    log.info("início da Experimentação 1")
    resumo = {"executado_em": datetime.now(UTC).isoformat(), "ativos": ATIVOS, "intervalo": INTERVALO}

    with httpx.Client(base_url=URL_BASE, timeout=10) as http:
        resumo["rest"] = passo_1_a_4(ClienteBinance(http=http))
    resumo["falhas_rest"] = passo_6()
    resumo["websocket"] = asyncio.run(passo_5(segundos_ws))
    resumo["falhas_websocket"] = asyncio.run(reconexao_simulada())

    (PASTA / "resumo.json").write_text(json.dumps(resumo, indent=2, ensure_ascii=False),
                                       encoding="utf-8")
    log.info("fim; resumo em %s", PASTA / "resumo.json")


if __name__ == "__main__":
    main()
