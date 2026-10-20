"""Perfil de risco, preferências de alerta (RF-011) e lista de ativos
acompanhados (RF-015). Perfil e identificadores de canal são dados pessoais e
ficam cifrados no banco (RNE-005)."""

from datetime import UTC, datetime

from nox.domain.contas import (
    CANAIS,
    FREQUENCIAS,
    MAX_LISTA,
    PERFIS,
    ErroDeConta,
    Usuario,
    normalizar_telegram,
    validar_frequencia,
    validar_perfil,
)
from nox.infrastructure.contas_repo import RepositorioContas
from nox.infrastructure.seguranca import Cifra


class ServicoPerfil:
    def __init__(self, repo: RepositorioContas, cifra: Cifra, ativos: dict[str, str],
                 agora=lambda: datetime.now(UTC)):
        self.repo = repo
        self.cifra = cifra
        self.agora = agora
        self.repo.garantir_ativos(ativos)

    # --- RF-011 ----------------------------------------------------------------

    def preferencias(self, u: Usuario) -> dict:
        canais = {c: {"ativo": False} for c in CANAIS}
        for canal, ativa, ident in self.repo.preferencias(u.id):
            canais[canal] = {"ativo": ativa}
            if canal == "telegram" and ident:
                canais[canal]["usuario"] = self.cifra.decifrar(ident)
        perfil = self.cifra.decifrar(u.perfil_risco_cifrado) if u.perfil_risco_cifrado else None
        return {"perfil_risco": perfil, "frequencia": u.frequencia_alerta, "canais": canais}

    def salvar_preferencias(self, u: Usuario, perfil: str | None, frequencia: str, canais: dict) -> dict:
        perfil = validar_perfil(perfil)
        frequencia = validar_frequencia(frequencia)
        if set(canais) - set(CANAIS):
            raise ErroDeConta("Canal de alerta desconhecido.")

        telegram = canais.get("telegram", {})
        usuario_telegram = None
        if telegram.get("ativo"):
            usuario_telegram = normalizar_telegram(telegram.get("usuario") or "")
        elif telegram.get("usuario"):
            usuario_telegram = normalizar_telegram(telegram["usuario"])

        u.perfil_risco_cifrado = self.cifra.cifrar(perfil) if perfil else None
        u.frequencia_alerta = frequencia
        self.repo.atualizar_usuario(u)
        self.repo.salvar_preferencia(u.id, "push", bool(canais.get("push", {}).get("ativo")), None)
        self.repo.salvar_preferencia(u.id, "telegram", bool(telegram.get("ativo")),
                                     self.cifra.cifrar(usuario_telegram) if usuario_telegram else None)
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
        """Tudo o que o Nox guarda sobre a pessoa, já decifrado. Ficam de fora
        só o hash da senha e o segredo do 2FA, que não servem ao titular e
        enfraqueceriam a conta se o arquivo vazasse."""
        prefs = self.preferencias(u)
        return {
            "conta": {"nome": u.nome, "email": u.email, "criada_em": u.criado_em.isoformat(),
                      "verificacao_em_duas_etapas": u.totp_ativo},
            "perfil_de_risco": prefs["perfil_risco"],
            "perfil_descricao": PERFIS.get(prefs["perfil_risco"]),
            "alertas": {"frequencia": FREQUENCIAS[prefs["frequencia"]], "canais": prefs["canais"]},
            "ativos_acompanhados": [{"ativo": s, "adicionado_em": d.isoformat()} for s, d in self.repo.lista(u.id)],
            "gerado_em": self.agora().isoformat(),
        }
