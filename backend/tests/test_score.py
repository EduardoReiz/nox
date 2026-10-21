from datetime import UTC, datetime, timedelta

import pytest

from nox.domain.mercado import Vela
from nox.domain.score import (
    AVISO_RISCO,
    LIMIAR_ACAO,
    PESOS,
    Componente,
    MedicaoSentimento,
    SemSinal,
    Sinal,
    combinar,
    explicar,
    forca_rsi,
    gerar_sinal,
)

AGORA = datetime(2026, 10, 20, 12, 30, tzinfo=UTC)
HORA = timedelta(hours=1)


def velas(fechamentos: list[float], atraso: timedelta = timedelta()) -> list[Vela]:
    """Série de 1 hora cuja última vela fechou logo antes de AGORA."""
    fim = AGORA.replace(minute=0) - HORA - atraso
    n = len(fechamentos)
    return [
        Vela("BTCUSDT", "1h", fim - (n - 1 - i) * HORA, p, p * 1.01, p * 0.99, p, 1.0, "binance")
        for i, p in enumerate(fechamentos)
    ]


def queda_forte() -> list[float]:
    """Preço estável e depois uma queda acelerada: RSI baixo e MACD negativo."""
    return [100 + (i % 3) * 0.2 for i in range(220)] + [100 * 0.985 ** i for i in range(1, 15)]


def alta_forte() -> list[float]:
    return [100 + (i % 3) * 0.2 for i in range(220)] + [100 * 1.015 ** i for i in range(1, 15)]


def sentimento(intensidade: float, validade: timedelta = HORA) -> MedicaoSentimento:
    medido = AGORA - timedelta(minutes=5)
    return MedicaoSentimento("BTCUSDT", "teste", intensidade, medido, medido + validade)


def comps(tec=None, sent=None, ml=None) -> list[Componente]:
    lista = []
    for nome, forca in (("tecnico", tec), ("sentimento", sent), ("ml", ml)):
        if forca is not None:
            lista.append(Componente(nome, forca, PESOS[nome]))
    return lista


# --- Regras do score, com as forças já prontas -------------------------------


def test_forca_rsi_classica():
    assert forca_rsi(30) == 1.0
    assert forca_rsi(70) == -1.0
    assert forca_rsi(50) == 0.0
    assert forca_rsi(10) == 1.0  # limitada a +1
    # Faixa neutra entre 40 e 60, e força crescendo até os extremos.
    assert forca_rsi(57) == 0.0 and forca_rsi(40) == 0.0
    assert forca_rsi(35) == pytest.approx(0.5)
    assert forca_rsi(65) == pytest.approx(-0.5)


def test_todos_concordando_com_forca_total_da_100():
    r = combinar(comps(1.0, 1.0, 1.0))
    assert (r.score, r.direcao, r.acao) == (100, "alta", "comprar")
    r = combinar(comps(-1.0, -1.0, -1.0))
    assert (r.score, r.direcao, r.acao) == (100, "baixa", "vender")


def test_score_e_a_media_ponderada_das_pontuacoes():
    # 0,5·80 + 0,3·50 + 0,2·0 (o ML aponta contra a direção, então vale 0) = 55
    r = combinar(comps(0.8, 0.5, -0.4))
    assert r.score == 55
    assert r.acao == "manter"


def test_limiar_de_60():
    r = combinar(comps(tec=0.6))
    assert (r.score, r.acao) == (60, "comprar")
    r = combinar(comps(tec=-0.59))
    assert (r.score, r.acao) == (59, "manter")


def test_tecnico_neutro_com_sentimento_e_ml_fortes():
    r = combinar(comps(0.0, 1.0, 1.0))
    assert r.score == 50
    assert r.acao == "manter"


def test_divergencia_critica_reduz_30_por_cento():
    r = combinar(comps(0.9, -0.5))
    # Pesos sem ML: 0,5/0,8 para o técnico. O sentimento aponta contra (S = 0).
    antes = 100 * 0.9 * 0.5 / 0.8
    assert r.divergencia == {"tecnico": "alta", "sentimento": "negativo",
                             "score_antes": round(antes), "reducao": 0.3}
    assert r.score == round(antes * 0.7)


def test_desacordo_fraco_nao_e_divergencia_critica():
    assert combinar(comps(0.9, -0.2)).divergencia is None
    assert combinar(comps(0.2, -0.9)).divergencia is None
    assert combinar(comps(0.9, 0.9)).divergencia is None


def test_abaixo_do_limiar_e_sempre_manter():
    valores = [-1.0, -0.6, -0.3, 0.0, 0.3, 0.6, 1.0]
    for t in valores:
        for se in valores + [None]:
            for ml in valores + [None]:
                r = combinar(comps(t, se, ml))
                assert 0 <= r.score <= 100
                if r.score < LIMIAR_ACAO:
                    assert r.acao == "manter"
                else:
                    assert r.acao == ("comprar" if r.direcao == "alta" else "vender")


# --- Geração do sinal a partir das velas ---------------------------------------


def test_historico_curto_nao_gera_sinal():
    r = gerar_sinal("BTCUSDT", velas([100.0] * 150), AGORA)
    assert isinstance(r, SemSinal)
    assert "histórico insuficiente" in r.motivo


def test_dados_desatualizados_nao_geram_sinal():
    r = gerar_sinal("BTCUSDT", velas(alta_forte(), atraso=3 * HORA), AGORA)
    assert isinstance(r, SemSinal)
    assert "desatualizados" in r.motivo


def test_todo_sinal_tem_explicacao_e_aviso():
    for serie in (queda_forte(), alta_forte(), [100.0] * 250):
        s = gerar_sinal("BTCUSDT", velas(serie), AGORA, [sentimento(0.9)], forca_ml=1.0)
        assert isinstance(s, Sinal)
        assert 0 <= s.score <= 100
        assert s.aviso_risco == AVISO_RISCO
        assert s.explicacao.startswith("Leitura do Nox para")


def test_queda_forte_isolada_e_neutra_no_tecnico():
    # Comportamento esperado da leitura clássica: na queda forte o RSI diz
    # "caiu demais, pode voltar" e o MACD diz "a queda tem força". Os dois se
    # anulam, e o Nox não manda vender no fundo nem comprar enquanto ainda cai.
    s = gerar_sinal("BTCUSDT", velas(queda_forte()), AGORA)
    d = s.componentes[0].detalhes
    assert d["forca_rsi"] > 0.9 and d["forca_macd"] < -0.9
    assert s.acao == "manter"


def test_preco_parado_e_neutro():
    s = gerar_sinal("BTCUSDT", velas([100.0] * 250), AGORA)
    assert (s.acao, s.direcao, s.score) == ("manter", "neutra", 0)
    assert "se anulam" in s.explicacao


def test_pesos_sao_redistribuidos_sem_ml_e_sem_sentimento():
    s = gerar_sinal("BTCUSDT", velas(alta_forte()), AGORA)
    assert s.ausentes == ["sentimento", "ml"]
    assert s.componentes[0].peso == pytest.approx(1.0)
    assert "não usou o sentimento de mercado nem a previsão de Machine Learning" in s.explicacao

    s = gerar_sinal("BTCUSDT", velas(alta_forte()), AGORA, [sentimento(0.5)])
    assert sum(c.peso for c in s.componentes) == pytest.approx(1.0)
    assert s.componentes[0].peso == pytest.approx(0.5 / 0.8)


def test_sentimento_expirado_nao_entra():
    expirado = MedicaoSentimento("BTCUSDT", "teste", 1.0, AGORA - 2 * HORA, AGORA - HORA)
    s = gerar_sinal("BTCUSDT", velas(alta_forte()), AGORA, [expirado])
    assert "sentimento" in s.ausentes


def test_divergencia_aparece_na_explicacao():
    detalhes = {"rsi": 28.0, "forca_macd": 0.8, "cruzamento": "alta"}
    componentes = [Componente("tecnico", 0.9, PESOS["tecnico"], detalhes=detalhes),
                   Componente("sentimento", -0.6, PESOS["sentimento"])]
    r = combinar(componentes)
    s = Sinal("BTCUSDT", AGORA, r.acao, r.score, r.direcao, componentes, ["ml"],
              r.divergencia, "")
    texto = explicar(s)
    assert "o gráfico aponta alta, mas o sentimento está negativo" in texto
    assert f"caiu de {r.divergencia['score_antes']} para {r.score}" in texto
    assert "abaixo de 30" in texto and "cruzar para cima" in texto
