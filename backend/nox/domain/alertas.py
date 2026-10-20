"""Quando um sinal vira alerta e o que a mensagem diz (RF-012, RF-013).

"Novo sinal" (RF-012) é entendido como **mudança de sugestão**: o ativo passou
de manter para comprar, de comprar para vender, e assim por diante. Repetir a
cada hora o mesmo "manter" faria o usuário ignorar os alertas. Decisão
provisória, a validar com os usuários.
"""

from dataclasses import dataclass

AVISO_CURTO = "Informativo, não é consultoria. O Nox não opera por você."

VERBOS = {"comprar": "sugere comprar", "vender": "sugere vender", "manter": "voltou a sugerir manter"}


@dataclass(frozen=True)
class Mudanca:
    ativo: str
    nome: str
    acao: str
    score: int
    acao_anterior: str | None
    explicacao: str
    sinal_id: int | None = None


def deve_alertar(acao_anterior: str | None, acao_nova: str) -> bool:
    """Primeiro sinal de um ativo só vira alerta se pedir ação; depois disso,
    toda mudança de sugestão vira alerta, inclusive a volta para manter (o
    usuário precisa saber que o sinal anterior perdeu força)."""
    if acao_anterior is None:
        return acao_nova != "manter"
    return acao_anterior != acao_nova


def moeda(ativo: str) -> str:
    return ativo.removesuffix("USDT")


def titulo(m: Mudanca) -> str:
    return f"{m.nome}: o Nox {VERBOS[m.acao]}"


def texto_curto(m: Mudanca) -> str:
    """Para a notificação push, que mostra poucas linhas."""
    return f"Confiança {m.score} de 100. Toque para ver por quê. {AVISO_CURTO}"


def texto_completo(m: Mudanca, link: str, aviso_risco: str) -> str:
    """Para o Telegram: explicação inteira, link e aviso de risco (RF-013)."""
    antes = f" (antes: {m.acao_anterior})" if m.acao_anterior else ""
    return (f"{titulo(m)}{antes}\nConfiança {m.score} de 100.\n\n{m.explicacao}\n\n"
            f"Veja os detalhes: {link}\n\n{aviso_risco}")


def resumo(mudancas: list[Mudanca], link: str, aviso_risco: str) -> tuple[str, str]:
    """Resumo diário para quem escolheu essa frequência."""
    linhas = [f"- {moeda(m.ativo)}: {m.acao} (confiança {m.score})" for m in mudancas]
    cab = "1 mudança" if len(mudancas) == 1 else f"{len(mudancas)} mudanças"
    return (f"Nox: {cab} nos seus ativos hoje",
            "Mudanças de sugestão nas últimas 24 horas:\n" + "\n".join(linhas)
            + f"\n\nVeja os detalhes: {link}\n\n{aviso_risco}")
