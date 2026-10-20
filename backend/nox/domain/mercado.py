"""Observação de mercado (seção 18.1) e validação das séries antes da gravação.

A camada domain não conhece a Binance nem os bancos: recebe velas já
convertidas para o formato interno e diz se a série está íntegra.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta

# Duração de cada intervalo aceito pelo Nox. Os nomes seguem a Binance porque
# é a única fonte por enquanto.
INTERVALOS = {
    "1m": timedelta(minutes=1),
    "5m": timedelta(minutes=5),
    "15m": timedelta(minutes=15),
    "1h": timedelta(hours=1),
    "4h": timedelta(hours=4),
    "1d": timedelta(days=1),
}


@dataclass(frozen=True)
class Vela:
    """Uma observação de mercado: preços e volume de um ativo num intervalo."""

    ativo: str
    intervalo: str
    instante: datetime  # abertura da vela, sempre em UTC
    abertura: float
    maxima: float
    minima: float
    fechamento: float
    volume: float
    fonte: str


@dataclass
class RelatorioValidacao:
    total: int = 0
    invalidas: list[str] = field(default_factory=list)
    duplicadas: list[datetime] = field(default_factory=list)
    fora_de_ordem: list[datetime] = field(default_factory=list)
    lacunas: list[tuple[datetime, datetime]] = field(default_factory=list)

    @property
    def integra(self) -> bool:
        return not (self.invalidas or self.duplicadas or self.fora_de_ordem or self.lacunas)


def problemas_da_vela(v: Vela) -> list[str]:
    """Regras que uma vela precisa cumprir para entrar na série."""
    erros = []
    if v.intervalo not in INTERVALOS:
        erros.append(f"intervalo desconhecido: {v.intervalo}")
    if v.instante.tzinfo is None:
        erros.append("instante sem fuso horário")
    precos = (v.abertura, v.maxima, v.minima, v.fechamento)
    if any(p <= 0 for p in precos):
        erros.append("preço menor ou igual a zero")
    if v.volume < 0:
        erros.append("volume negativo")
    if v.maxima < max(v.abertura, v.fechamento, v.minima):
        erros.append("máxima menor que outro preço da vela")
    if v.minima > min(v.abertura, v.fechamento, v.maxima):
        erros.append("mínima maior que outro preço da vela")
    return erros


def validar_serie(velas: list[Vela]) -> RelatorioValidacao:
    """Confere uma série de um único ativo e intervalo, na ordem recebida."""
    rel = RelatorioValidacao(total=len(velas))
    vistos: set[datetime] = set()
    anterior: Vela | None = None

    for v in velas:
        for erro in problemas_da_vela(v):
            rel.invalidas.append(f"{v.ativo} {v.instante.isoformat()}: {erro}")

        if v.instante in vistos:
            rel.duplicadas.append(v.instante)
            continue
        vistos.add(v.instante)

        if anterior is not None:
            passo = INTERVALOS.get(v.intervalo)
            if v.instante < anterior.instante:
                rel.fora_de_ordem.append(v.instante)
            elif passo and v.instante - anterior.instante > passo:
                rel.lacunas.append((anterior.instante, v.instante))
        anterior = v

    return rel


def limpar_serie(velas: list[Vela]) -> list[Vela]:
    """Ordena por tempo, tira duplicadas e descarta velas inválidas."""
    unicas: dict[datetime, Vela] = {}
    for v in velas:
        if not problemas_da_vela(v):
            unicas.setdefault(v.instante, v)
    return [unicas[t] for t in sorted(unicas)]
