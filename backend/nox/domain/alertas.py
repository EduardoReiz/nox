"""Quando um sinal vira alerta e o que a mensagem diz (RF-012, RF-013).

"Novo sinal" (RF-012) é entendido como **mudança de leitura**: o ativo passou
de neutro para sinal de alta, de sinal de alta para sinal de queda, e assim por diante. Repetir a
cada hora o mesmo "neutro" faria o usuário ignorar os alertas. Decisão
provisória, a validar com os usuários.
"""

from dataclasses import dataclass

from nox.domain.score import LEITURAS

AVISO_CURTO = "Informativo, não é recomendação nem consultoria. O Nox não opera por você."

TITULOS = {"comprar": "o Nox vê sinal de alta", "vender": "o Nox vê sinal de queda", "manter": "voltou ao neutro"}


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
    toda mudança de leitura vira alerta, inclusive a volta para neutro (o
    usuário precisa saber que o sinal anterior perdeu força)."""
    if acao_anterior is None:
        return acao_nova != "manter"
    return acao_anterior != acao_nova


def moeda(ativo: str) -> str:
    return ativo.removesuffix("USDT")


def titulo(m: Mudanca) -> str:
    return f"{m.nome}: {TITULOS[m.acao]}"


def texto_curto(m: Mudanca) -> str:
    """Para a notificação push, que mostra poucas linhas."""
    return f"Confiança {m.score} de 100. Toque para ver por quê. {AVISO_CURTO}"


def texto_completo(m: Mudanca, link: str, aviso_risco: str) -> str:
    """Para o Telegram: explicação inteira, link e aviso de risco (RF-013)."""
    antes = f" (antes: {LEITURAS[m.acao_anterior]})" if m.acao_anterior else ""
    return (f"{titulo(m)}{antes}\nConfiança {m.score} de 100.\n\n{m.explicacao}\n\n"
            f"Veja os detalhes: {link}\n\n{aviso_risco}")


def resumo(mudancas: list[Mudanca], link: str, aviso_risco: str) -> tuple[str, str]:
    """Resumo diário para quem escolheu essa frequência."""
    linhas = [f"- {moeda(m.ativo)}: {LEITURAS[m.acao]} (confiança {m.score})" for m in mudancas]
    cab = "1 mudança" if len(mudancas) == 1 else f"{len(mudancas)} mudanças"
    return (f"Nox: {cab} nos seus ativos hoje",
            "Mudanças de leitura nas últimas 24 horas:\n" + "\n".join(linhas)
            + f"\n\nVeja os detalhes: {link}\n\n{aviso_risco}")
