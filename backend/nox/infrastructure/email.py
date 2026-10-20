"""Envio de e-mail. Ainda não há servidor de e-mail no projeto: em
desenvolvimento a mensagem é escrita no log do backend."""

import logging
from typing import Protocol

log = logging.getLogger("nox.email")


class CaixaDeSaida(Protocol):
    def enviar(self, para: str, assunto: str, texto: str) -> None: ...


class EmailNoLog:
    def enviar(self, para, assunto, texto):
        log.warning("E-MAIL (desenvolvimento) para %s | %s\n%s", para, assunto, texto)


class EmailMemoria:
    def __init__(self):
        self.enviados: list[tuple[str, str, str]] = []

    def enviar(self, para, assunto, texto):
        self.enviados.append((para, assunto, texto))
