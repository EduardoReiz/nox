"""Processo que roda em segundo plano: gera os sinais, envia os alertas e
atende o bot do Telegram (RF-008, RF-012). No diagrama de casos de uso, é o
"sistema" que dispara a geração de sinais periodicamente.

    python -m nox.worker
"""

import logging
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from nox.api.contas import servico_alertas

HORA_DO_RESUMO = 9  # horário de Brasília
INTERVALO_S = 60

log = logging.getLogger("nox.worker")


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    alertas = servico_alertas()
    log.info("worker iniciado; push=%s telegram=%s", bool(alertas.push), bool(alertas.telegram))
    ultimo_resumo = None
    while True:
        inicio = time.monotonic()
        try:
            alertas.ciclo()
            hoje = datetime.now(ZoneInfo("America/Sao_Paulo"))
            if hoje.hour >= HORA_DO_RESUMO and ultimo_resumo != hoje.date():
                log.info("resumos enviados: %d", alertas.enviar_resumos())
                ultimo_resumo = hoje.date()
        except Exception:
            log.exception("falha no ciclo; tenta de novo no próximo")
        # Com Telegram, a espera vira long polling: responde ao /start na hora.
        while (resta := INTERVALO_S - (time.monotonic() - inicio)) > 1:
            if alertas.telegram:
                try:
                    alertas.processar_telegram(espera=int(min(resta, 25)))
                except Exception:
                    log.exception("falha ao ler o Telegram")
                    time.sleep(5)
            else:
                time.sleep(resta)


if __name__ == "__main__":
    main()
