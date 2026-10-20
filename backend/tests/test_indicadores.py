import pytest

from nox.domain.indicadores import HistoricoInsuficiente, macd, mme, rsi

# Exemplo clássico de RSI da StockCharts (planilha "cs-rsi"), muito usado para
# conferir implementações da suavização de Wilder. A planilha exibe os preços
# com duas casas, mas calcula com quatro; com duas casas o primeiro RSI dá 70,46.
PRECOS_STOCKCHARTS = [
    44.3389, 44.0902, 44.1497, 43.6124, 44.3278, 44.8264, 45.0955, 45.4245, 45.8433, 46.0826,
    45.8931, 46.0328, 45.6140, 46.2820, 46.2820, 46.0028, 46.0328, 46.4116, 46.2222, 45.6439,
]
RSI_STOCKCHARTS = [70.53, 66.32, 66.55, 69.41, 66.36, 57.97]


def test_rsi_bate_com_valores_de_referencia():
    valores = rsi(PRECOS_STOCKCHARTS)
    assert valores[:14] == [None] * 14
    for calculado, esperado in zip(valores[14:], RSI_STOCKCHARTS):
        assert calculado == pytest.approx(esperado, abs=0.01)


def test_rsi_sempre_em_alta_e_100():
    assert rsi([float(p) for p in range(1, 31)])[-1] == 100.0


def test_rsi_sempre_em_baixa_e_0():
    assert rsi([float(p) for p in range(30, 0, -1)])[-1] == pytest.approx(0.0)


def test_rsi_preco_constante_e_50():
    assert rsi([10.0] * 20)[-1] == 50.0


def test_rsi_fica_entre_0_e_100():
    precos = [100 + (i % 7) * 3 - (i % 5) * 4 for i in range(200)]
    assert all(0 <= v <= 100 for v in rsi(precos) if v is not None)


def test_rsi_exige_15_precos():
    with pytest.raises(HistoricoInsuficiente):
        rsi([1.0] * 14)
    rsi([1.0] * 15)


def test_mme_comeca_pela_media_simples():
    valores = mme([1.0, 2.0, 3.0, 4.0], 3)
    assert valores[:2] == [None, None]
    assert valores[2] == 2.0
    assert valores[3] == pytest.approx(0.5 * 4 + 0.5 * 2.0)


def test_macd_exige_35_precos_e_alinha_as_series():
    with pytest.raises(HistoricoInsuficiente):
        macd([1.0] * 34)
    r = macd([float(p) for p in range(1, 36)])
    assert len(r.macd) == len(r.sinal) == len(r.histograma) == 35
    assert r.macd[24] is None and r.macd[25] is not None
    assert r.sinal[32] is None and r.sinal[33] is not None


def test_macd_preco_constante_e_zero():
    r = macd([50.0] * 60)
    assert r.macd[-1] == pytest.approx(0.0)
    assert r.histograma[-1] == pytest.approx(0.0)
    assert r.cruzamento is None


def test_macd_tendencia_de_alta_fica_positivo():
    r = macd([100 * 1.01 ** i for i in range(80)])
    assert r.macd[-1] > 0


def test_macd_detecta_cruzamento_de_alta():
    # Queda longa e depois uma alta forte: o histograma vira de negativo para
    # positivo em algum ponto, e cortando a série ali o cruzamento aparece.
    precos = [100 - i * 0.5 for i in range(60)] + [70 + i * 2 for i in range(30)]
    hist = macd(precos).histograma
    virada = next(i for i in range(1, len(hist))
                  if hist[i - 1] is not None and hist[i - 1] <= 0 < hist[i])
    assert macd(precos[: virada + 1]).cruzamento == "alta"


def test_macd_detecta_cruzamento_de_baixa():
    precos = [50 + i * 0.5 for i in range(60)] + [80 - i * 2 for i in range(30)]
    hist = macd(precos).histograma
    virada = next(i for i in range(1, len(hist))
                  if hist[i - 1] is not None and hist[i - 1] >= 0 > hist[i])
    assert macd(precos[: virada + 1]).cruzamento == "baixa"
