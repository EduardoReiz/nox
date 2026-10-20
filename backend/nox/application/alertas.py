"""Geração periódica de sinais e envio dos alertas (RF-012, RF-008, RF-013).

O ciclo roda a cada minuto no worker (nox/worker.py):
1. calcula o sinal de cada ativo; cada vela de 1 hora fechada gera no máximo
   um Sinal de Recomendação gravado no banco (RF-008, RNF-005);
2. se a sugestão mudou em relação ao sinal anterior, vira alerta;
3. o alerta vai para quem acompanha o ativo (RF-015): na hora, pelos canais
   ligados, ou guardado para o resumo diário, conforme a preferência (RF-011).
"""

import json
import logging
from collections.abc import Callable
from datetime import UTC, datetime

from nox.application.perfil import ServicoPerfil
from nox.domain import alertas as regras
from nox.domain.alertas import Mudanca
from nox.domain.contas import Usuario
from nox.domain.score import AVISO_RISCO
from nox.infrastructure.contas_repo import RepositorioContas
from nox.infrastructure.notificacoes import CanalPush, ClienteTelegram, InscricaoExpirada
from nox.infrastructure.sinais_repo import RepositorioSinais

log = logging.getLogger(__name__)


class ServicoAlertas:
    def __init__(self, contas: RepositorioContas, sinais: RepositorioSinais, perfil: ServicoPerfil,
                 gerar: Callable[[], list[tuple[dict, datetime]]], push: CanalPush | None,
                 telegram: ClienteTelegram | None, url_app: str = "http://localhost:5173",
                 agora=lambda: datetime.now(UTC)):
        self.contas = contas
        self.sinais = sinais
        self.perfil = perfil
        self.gerar = gerar
        self.push = push
        self.telegram = telegram
        self.url_app = url_app
        self.agora = agora
        self._ultimo_update = 0

    # --- 1 e 2: sinais novos e mudanças ----------------------------------------

    def ciclo(self) -> list[Mudanca]:
        mudancas = []
        for sinal, vela in self.gerar():
            if not sinal.get("disponivel"):
                continue
            anterior = self.sinais.ultimo(sinal["ativo"])
            sinal_id = self.sinais.salvar(sinal, vela)
            if sinal_id is None:
                continue  # esta vela já foi processada
            acao_anterior = anterior["acao"] if anterior else None
            if regras.deve_alertar(acao_anterior, sinal["acao"]):
                m = Mudanca(sinal["ativo"], sinal["nome"], sinal["acao"], sinal["score"], acao_anterior,
                            sinal["explicacao"], sinal_id)
                mudancas.append(m)
                log.info("mudança em %s: %s -> %s", m.ativo, acao_anterior, m.acao)
        for m in mudancas:
            self._distribuir(m)
        return mudancas

    # --- 3: entrega ---------------------------------------------------------------

    def _link(self, ativo: str | None = None) -> str:
        return f"{self.url_app}/sinais/{ativo}" if ativo else f"{self.url_app}/sinais"

    def _distribuir(self, m: Mudanca) -> None:
        for uid in self.contas.seguidores(m.ativo):
            u = self.contas.usuario_por_id(uid)
            if u is None or not any(self.perfil.destino(uid, c) for c in ("push", "telegram")):
                continue
            if u.frequencia_alerta == "resumo_diario":
                self.sinais.registrar_alerta(uid, m.sinal_id, "resumo", "pendente", self.agora())
            else:
                self._entregar(u, regras.titulo(m), regras.texto_curto(m),
                               regras.texto_completo(m, self._link(m.ativo), AVISO_RISCO),
                               self._link(m.ativo), m.sinal_id)

    def _entregar(self, u: Usuario, titulo: str, curto: str, completo: str, link: str,
                  sinal_id: int | None) -> dict[str, str]:
        resultado = {}
        inscricao = self.perfil.destino(u.id, "push")
        if inscricao and self.push:
            resultado["push"] = self._tentar(u.id, "push", sinal_id,
                                             lambda: self.push.enviar(json.loads(inscricao), titulo, curto, link))
        chat = self.perfil.destino(u.id, "telegram")
        if chat and self.telegram:
            resultado["telegram"] = self._tentar(u.id, "telegram", sinal_id,
                                                 lambda: self.telegram.enviar(chat, completo))
        return resultado

    def _tentar(self, uid: str, canal: str, sinal_id: int | None, enviar) -> str:
        try:
            enviar()
        except InscricaoExpirada:
            self.perfil.desconectar(uid, canal)
            status, erro = "falhou", "inscrição cancelada pelo navegador; canal desconectado"
        except Exception as e:  # noqa: BLE001 - uma falha de canal não pode parar os outros envios
            log.warning("falha ao enviar por %s: %s", canal, e)
            status, erro = "falhou", str(e)[:300]
        else:
            status, erro = "enviado", None
        if sinal_id is not None:
            self.sinais.registrar_alerta(uid, sinal_id, canal, status, self.agora(), erro)
        return "enviado" if status == "enviado" else f"falhou: {erro}"

    def enviar_resumos(self) -> int:
        """Manda o resumo diário a quem tem mudanças pendentes."""
        enviados = 0
        for uid, sinais in self.sinais.pendentes_resumo().items():
            u = self.contas.usuario_por_id(uid)
            if u is None:
                continue
            mudancas = [Mudanca(s["ativo"], s["ativo"], s["acao"], s["score"], None, s["explicacao"])
                        for s in sinais]
            titulo, texto = regras.resumo(mudancas, self._link(), AVISO_RISCO)
            self._entregar(u, titulo, texto.split("\n\n")[0], texto, self._link(), None)
            self.sinais.marcar_resumo_enviado(uid, self.agora())
            enviados += 1
        return enviados

    def testar(self, u: Usuario) -> dict[str, str]:
        """Alerta de teste, para a pessoa conferir que os canais funcionam."""
        titulo = "Nox: alerta de teste"
        texto = "Se você está lendo isto, os alertas do Nox chegam aqui."
        return self._entregar(u, titulo, texto, f"{texto}\n\n{AVISO_RISCO}", self._link(), None)

    # --- Telegram: ligar conta e chat ---------------------------------------------

    def processar_telegram(self, espera: int = 0) -> int:
        """Lê as mensagens recebidas pelo bot. "/start <código>" liga a conta."""
        if not self.telegram:
            return 0
        tratadas = 0
        for update in self.telegram.novidades(self._ultimo_update + 1, espera):
            self._ultimo_update = update["update_id"]
            msg = update.get("message") or {}
            texto, chat = (msg.get("text") or "").strip(), (msg.get("chat") or {}).get("id")
            if not chat:
                continue
            tratadas += 1
            partes = texto.split(maxsplit=1)
            if partes[:1] == ["/start"] and len(partes) == 2:
                u = self.perfil.vincular_telegram(partes[1], str(chat))
                resposta = (f"Pronto, {u.nome}! Os alertas do Nox sobre os ativos que você acompanha vão chegar "
                            "aqui.\n\n" + AVISO_RISCO) if u else (
                            "Este link expirou ou já foi usado. Gere outro na tela Conta do Nox.")
            else:
                resposta = ("Olá! Eu envio os alertas do Nox. Para receber, entre na sua conta no Nox, "
                            "abra a tela Conta e toque em Conectar Telegram.")
            try:
                self.telegram.enviar(str(chat), resposta)
            except Exception as e:  # noqa: BLE001
                log.warning("falha ao responder no Telegram: %s", e)
        return tratadas
