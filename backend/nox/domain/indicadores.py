"""RSI e MACD escritos à mão (RF-003, Experimentação 4).

As funções devolvem uma lista do mesmo tamanho da série de preços, com None
nas posições em que ainda não há histórico suficiente. Assim cada valor fica
alinhado com a vela que o gerou.

As médias começam pela média simples dos primeiros períodos, e não pelo
primeiro preço. É o mesmo ponto de partida usado pelas plataformas de gráfico,
e corrige a diferença apontada na revisão do protótipo de referência.
"""

from dataclasses import dataclass


class HistoricoInsuficiente(ValueError):
    """Há menos preços do que o indicador precisa (RNE-004)."""


def _exigir(precos: list[float], minimo: int, nome: str) -> None:
    if len(precos) < minimo:
        raise HistoricoInsuficiente(
            f"{nome} precisa de pelo menos {minimo} preços; recebeu {len(precos)}"
        )


def rsi(precos: list[float], periodo: int = 14) -> list[float | None]:
    """Índice de Força Relativa com a suavização de Wilder.

    O primeiro valor sai na posição `periodo`, porque são necessárias
    `periodo` variações, e cada variação usa dois preços.
    """
    _exigir(precos, periodo + 1, "RSI")

    ganhos, perdas = [], []
    for anterior, atual in zip(precos, precos[1:]):
        variacao = atual - anterior
        ganhos.append(max(variacao, 0.0))
        perdas.append(max(-variacao, 0.0))

    def calcula(media_ganho: float, media_perda: float) -> float:
        if media_perda == 0:
            # Sem nenhuma queda o RSI é 100; preço parado não indica nada (50).
            return 100.0 if media_ganho > 0 else 50.0
        rs = media_ganho / media_perda
        return 100 - 100 / (1 + rs)

    resultado: list[float | None] = [None] * periodo
    media_ganho = sum(ganhos[:periodo]) / periodo
    media_perda = sum(perdas[:periodo]) / periodo
    resultado.append(calcula(media_ganho, media_perda))

    for g, p in zip(ganhos[periodo:], perdas[periodo:]):
        media_ganho = (media_ganho * (periodo - 1) + g) / periodo
        media_perda = (media_perda * (periodo - 1) + p) / periodo
        resultado.append(calcula(media_ganho, media_perda))

    return resultado


def mme(valores: list[float], periodo: int) -> list[float | None]:
    """Média móvel exponencial, começando pela média simples."""
    _exigir(valores, periodo, "MME")
    alfa = 2 / (periodo + 1)
    resultado: list[float | None] = [None] * (periodo - 1)
    media = sum(valores[:periodo]) / periodo
    resultado.append(media)
    for v in valores[periodo:]:
        media = alfa * v + (1 - alfa) * media
        resultado.append(media)
    return resultado


@dataclass
class ResultadoMACD:
    macd: list[float | None]
    sinal: list[float | None]
    histograma: list[float | None]
    cruzamento: str | None  # "alta", "baixa" ou None, olhando a última vela


def macd(precos: list[float], rapida: int = 12, lenta: int = 26, sinal: int = 9) -> ResultadoMACD:
    """MACD 12/26/9.

    Com 12/26/9 a linha MACD começa na posição 25 e a linha de sinal na 33.
    Para dizer se houve cruzamento é preciso comparar com a vela anterior,
    por isso o mínimo é 35 preços, como diz a RNE-004.
    """
    minimo = lenta + sinal
    _exigir(precos, minimo, "MACD")

    mme_rapida = mme(precos, rapida)
    mme_lenta = mme(precos, lenta)
    linha = [
        r - l if r is not None and l is not None else None
        for r, l in zip(mme_rapida, mme_lenta)
    ]

    inicio = lenta - 1
    sinal_parcial = mme([v for v in linha[inicio:] if v is not None], sinal)
    linha_sinal = [None] * inicio + sinal_parcial

    histograma = [
        m - s if m is not None and s is not None else None
        for m, s in zip(linha, linha_sinal)
    ]

    cruzamento = None
    h_ant, h_atual = histograma[-2], histograma[-1]
    if h_ant is not None and h_atual is not None:
        if h_ant <= 0 < h_atual:
            cruzamento = "alta"
        elif h_ant >= 0 > h_atual:
            cruzamento = "baixa"

    return ResultadoMACD(linha, linha_sinal, histograma, cruzamento)
