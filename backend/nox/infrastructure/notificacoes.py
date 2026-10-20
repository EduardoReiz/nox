"""Canais de entrega dos alertas (RF-012): notificação push e Telegram."""

import json
import logging

import httpx
from pywebpush import WebPushException, webpush

log = logging.getLogger(__name__)


class InscricaoExpirada(Exception):
    """O navegador cancelou a inscrição (desinstalou, limpou dados). Deve ser
    apagada para não insistir."""


class CanalPush:
    """Web Push (padrão do W3C): funciona no Chrome, Firefox, Edge e no Safari
    do iPhone com o site adicionado à tela inicial. Não depende de conta em
    serviço externo, só do par de chaves VAPID do Nox."""

    def __init__(self, chave_privada: str, contato: str, enviar=webpush):
        self.chave_privada = chave_privada
        self.contato = contato
        self._enviar = enviar

    def enviar(self, inscricao: dict, titulo: str, texto: str, url: str) -> None:
        try:
            self._enviar(
                subscription_info=inscricao,
                data=json.dumps({"titulo": titulo, "texto": texto, "url": url}, ensure_ascii=False),
                vapid_private_key=self.chave_privada,
                vapid_claims={"sub": self.contato},
                ttl=6 * 3600,  # um sinal velho de mais de 6 h não serve mais
            )
        except WebPushException as e:
            if e.response is not None and e.response.status_code in (404, 410):
                raise InscricaoExpirada() from e
            raise


class ClienteTelegram:
    """API de bots do Telegram. Sem token, o canal fica desligado."""

    def __init__(self, token: str, http: httpx.Client | None = None):
        self.token = token
        self.http = http or httpx.Client(base_url=f"https://api.telegram.org/bot{token}/", timeout=35)

    def enviar(self, chat_id: str, texto: str) -> None:
        r = self.http.post("sendMessage", json={"chat_id": chat_id, "text": texto,
                                                "disable_web_page_preview": True})
        dados = r.json()
        if not dados.get("ok"):
            raise RuntimeError(f"Telegram recusou: {dados.get('description', r.status_code)}")

    def novidades(self, desde: int, espera: int = 0) -> list[dict]:
        """Mensagens recebidas pelo bot desde o update `desde` (long polling)."""
        r = self.http.get("getUpdates", params={"offset": desde, "timeout": espera,
                                                "allowed_updates": json.dumps(["message"])})
        dados = r.json()
        if not dados.get("ok"):
            raise RuntimeError(f"Telegram recusou: {dados.get('description', r.status_code)}")
        return dados["result"]
