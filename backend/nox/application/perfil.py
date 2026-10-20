"""Perfil de risco, preferências de alerta (RF-011) e lista de ativos
acompanhados (RF-015). Perfil e identificadores de canal são dados pessoais e
ficam cifrados no banco (RNE-005).

Cada canal precisa estar **conectado** antes de ser ligado:
- push: o navegador entrega uma inscrição (endpoint e chaves) quando o
  usuário permite as notificações;
- Telegram: o bot só pode escrever para quem iniciou a conversa com ele. A
  pessoa abre um link com um código de uso único, e o bot guarda o chat.
"""

import json
from datetime import UTC, datetime, timedelta

from nox.domain.contas import (
    CANAIS,
    FREQUENCIAS,
    MAX_LISTA,
    PERFIS,
    ErroDeConta,
    Usuario,
    validar_frequencia,
    validar_perfil,
)
from nox.infrastructure import seguranca
from nox.infrastructure.contas_repo import RepositorioContas
from nox.infrastructure.seguranca import Cifra

DURACAO_VINCULO_TELEGRAM = timedelta(minutes=15)


class ServicoPerfil:
    def __init__(self, repo: RepositorioContas, cifra: Cifra, ativos: dict[str, str],
                 agora=lambda: datetime.now(UTC)):
        self.repo = repo
        self.cifra = cifra
        self.agora = agora
        self.repo.garantir_ativos(ativos)

    # --- canais ---------------------------------------------------------------

    def _canais(self, usuario_id: str) -> dict[str, tuple[bool, str | None]]:
        canais = {c: (False, None) for c in CANAIS}
        for canal, ativa, ident in self.repo.preferencias(usuario_id):
            canais[canal] = (ativa, ident)
        return canais

    def destino(self, usuario_id: str, canal: str) -> str | None:
        """Identificador decifrado do canal, só se estiver conectado e ligado."""
        ativa, ident = self._canais(usuario_id)[canal]
        return self.cifra.decifrar(ident) if ativa and ident else None

    def conectar_push(self, u: Usuario, inscricao: dict) -> None:
        endpoint = inscricao.get("endpoint", "")
        chaves = inscricao.get("keys") or {}
        if not endpoint.startswith("https://") or not chaves.get("p256dh") or not chaves.get("auth"):
            raise ErroDeConta("O navegador não entregou uma inscrição de notificação válida.")
        dados = {"endpoint": endpoint, "keys": {"p256dh": chaves["p256dh"], "auth": chaves["auth"]}}
        self.repo.salvar_preferencia(u.id, "push", True, self.cifra.cifrar(json.dumps(dados)))
        self.repo.registrar("push_conectado", u.id, self.agora())

    def desconectar(self, u_id: str, canal: str) -> None:
        self.repo.salvar_preferencia(u_id, canal, False, None)

    def iniciar_vinculo_telegram(self, u: Usuario) -> str:
        """Código de uso único que vai no link t.me/<bot>?start=<código>."""
        token = seguranca.novo_token()
        self.repo.apagar_desafios(u.id, "telegram")
        self.repo.criar_desafio("telegram", seguranca.resumo(token), u.id,
                                self.agora() + DURACAO_VINCULO_TELEGRAM)
        return token

    def vincular_telegram(self, token: str, chat_id: str) -> Usuario | None:
        uid = self.repo.usuario_do_desafio("telegram", seguranca.resumo(token), self.agora())
        if not uid:
            return None
        self.repo.salvar_preferencia(uid, "telegram", True, self.cifra.cifrar(str(chat_id)))
        self.repo.apagar_desafios(uid, "telegram")
        self.repo.registrar("telegram_conectado", uid, self.agora())
        return self.repo.usuario_por_id(uid)

    # --- RF-011 ----------------------------------------------------------------

    def preferencias(self, u: Usuario) -> dict:
        canais = {c: {"ativo": ativa, "conectado": ident is not None}
                  for c, (ativa, ident) in self._canais(u.id).items()}
        perfil = self.cifra.decifrar(u.perfil_risco_cifrado) if u.perfil_risco_cifrado else None
        return {"perfil_risco": perfil, "frequencia": u.frequencia_alerta, "canais": canais}

    def salvar_preferencias(self, u: Usuario, perfil: str | None, frequencia: str, canais: dict) -> dict:
        perfil = validar_perfil(perfil)
        frequencia = validar_frequencia(frequencia)
        if set(canais) - set(CANAIS):
            raise ErroDeConta("Canal de alerta desconhecido.")
        atuais = self._canais(u.id)
        for canal, pedido in canais.items():
            ligar = bool(pedido.get("ativo"))
            if ligar and atuais[canal][1] is None:
                nome = "as notificações" if canal == "push" else "o Telegram"
                raise ErroDeConta(f"Conecte {nome} antes de ligar esse alerta.")

        u.perfil_risco_cifrado = self.cifra.cifrar(perfil) if perfil else None
        u.frequencia_alerta = frequencia
        self.repo.atualizar_usuario(u)
        for canal, pedido in canais.items():
            self.repo.salvar_preferencia(u.id, canal, bool(pedido.get("ativo")), atuais[canal][1])
        self.repo.registrar("preferencias_alteradas", u.id, self.agora())
        return self.preferencias(u)

    # --- RF-015 ----------------------------------------------------------------

    def lista(self, u: Usuario) -> list[str]:
        return [simbolo for simbolo, _ in self.repo.lista(u.id)]

    def salvar_lista(self, u: Usuario, simbolos: list[str]) -> list[str]:
        disponiveis = self.repo.ativos()
        unicos = list(dict.fromkeys(s.upper() for s in simbolos))
        desconhecidos = [s for s in unicos if s not in disponiveis]
        if desconhecidos:
            raise ErroDeConta(f"O Nox ainda não acompanha: {', '.join(desconhecidos)}.")
        if len(unicos) > MAX_LISTA:
            raise ErroDeConta(f"A lista pode ter até {MAX_LISTA} ativos.")
        self.repo.salvar_lista(u.id, unicos, self.agora())
        return self.lista(u)

    # --- LGPD: consultar os próprios dados -------------------------------------

    def meus_dados(self, u: Usuario) -> dict:
        """Tudo o que o Nox guarda sobre a pessoa, já decifrado. Ficam de fora o
        hash da senha, o segredo do 2FA e as chaves técnicas da inscrição de
        notificação, que não servem ao titular e enfraqueceriam a conta se o
        arquivo vazasse."""
        prefs = self.preferencias(u)
        canais = {c: {"ligado": v["ativo"], "conectado": v["conectado"]} for c, v in prefs["canais"].items()}
        telegram = self.destino(u.id, "telegram")
        if telegram:
            canais["telegram"]["chat"] = telegram
        return {
            "conta": {"nome": u.nome, "email": u.email, "criada_em": u.criado_em.isoformat(),
                      "verificacao_em_duas_etapas": u.totp_ativo},
            "perfil_de_risco": prefs["perfil_risco"],
            "perfil_descricao": PERFIS.get(prefs["perfil_risco"]),
            "alertas": {"frequencia": FREQUENCIAS[prefs["frequencia"]], "canais": canais},
            "ativos_acompanhados": [{"ativo": s, "adicionado_em": d.isoformat()} for s, d in self.repo.lista(u.id)],
            "gerado_em": self.agora().isoformat(),
        }
