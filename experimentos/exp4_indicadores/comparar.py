"""Experimentação 4 (parte dos indicadores): RSI e MACD do Nox x biblioteca `ta`.

Usa as velas de 1 hora gravadas pela Experimentação 1. Rodar a partir da
pasta backend, com o ambiente ativado:

    python ../experimentos/exp4_indicadores/comparar.py
"""

import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD

from nox.domain.indicadores import macd, rsi

RAIZ = Path(__file__).parent
VELAS = RAIZ.parent / "exp1_ingestao_binance" / "evidencias"
PASTA = RAIZ / "evidencias"
ATIVOS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
# Depois de quantas velas as duas implementações deveriam concordar. A `ta`
# começa as médias pelo primeiro preço; o Nox, pela média simples. A diferença
# some aos poucos, e 200 velas são mais que suficientes.
AQUECIMENTO = 200


def diferencas(nox: list, ref: pd.Series, a_partir: int) -> dict:
    serie_nox = pd.Series(nox, dtype="float64")
    dif = (serie_nox - ref).abs()
    return {
        "maior_diferenca_logo_no_inicio": round(float(dif.dropna().iloc[:10].max()), 6),
        "maior_diferenca_apos_aquecimento": round(float(dif.iloc[a_partir:].max()), 10),
        "ultimo_valor_nox": round(float(serie_nox.iloc[-1]), 4),
        "ultimo_valor_ta": round(float(ref.iloc[-1]), 4),
    }


def main():
    PASTA.mkdir(exist_ok=True)
    resultado = {"executado_em": datetime.now(UTC).isoformat(), "aquecimento": AQUECIMENTO}

    for ativo in ATIVOS:
        df = pd.read_csv(VELAS / f"velas_{ativo}_1h.csv", parse_dates=["instante"])
        precos = df["fechamento"].tolist()

        rsi_nox = rsi(precos)
        rsi_ta = RSIIndicator(df["fechamento"], window=14).rsi()

        m = macd(precos)
        macd_ta = MACD(df["fechamento"], window_fast=12, window_slow=26, window_sign=9)

        resultado[ativo] = {
            "velas": len(df),
            "de": df["instante"].iloc[0].isoformat(),
            "ate": df["instante"].iloc[-1].isoformat(),
            "rsi": diferencas(rsi_nox, rsi_ta, AQUECIMENTO),
            "macd": diferencas(m.macd, macd_ta.macd(), AQUECIMENTO),
            "linha_de_sinal": diferencas(m.sinal, macd_ta.macd_signal(), AQUECIMENTO),
            "histograma": diferencas(m.histograma, macd_ta.macd_diff(), AQUECIMENTO),
            "cruzamento_na_ultima_vela": m.cruzamento,
        }

        tabela = pd.DataFrame({
            "instante": df["instante"], "fechamento": df["fechamento"],
            "rsi_nox": rsi_nox, "rsi_ta": rsi_ta,
            "macd_nox": m.macd, "macd_ta": macd_ta.macd(),
            "sinal_nox": m.sinal, "sinal_ta": macd_ta.macd_signal(),
            "histograma_nox": m.histograma, "histograma_ta": macd_ta.macd_diff(),
        })
        tabela.to_csv(PASTA / f"comparacao_{ativo}.csv", index=False, float_format="%.6f")
        print(ativo, json.dumps(resultado[ativo]["rsi"]), json.dumps(resultado[ativo]["macd"]))

    (PASTA / "resumo.json").write_text(json.dumps(resultado, indent=2, ensure_ascii=False),
                                       encoding="utf-8")


if __name__ == "__main__":
    main()
