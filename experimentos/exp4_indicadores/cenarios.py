"""Experimentação 4 (parte do score): planilha de cenários e teste com dados reais.

1. Cenários controlados: forças escolhidas à mão, com e sem divergência,
   com e sem sentimento e ML, gravados em evidencias/cenarios_score.csv.
2. Dados reais: para cada hora das velas da Experimentação 1 (a partir da
   vela 200), calcula o componente técnico e o sinal que o Nox daria só com
   ele, para ver com que frequência o limiar de 60 é atingido.

Rodar a partir da pasta backend, com o ambiente ativado:

    python ../experimentos/exp4_indicadores/cenarios.py
"""

import csv
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from nox.domain.score import MINIMO_VELAS, PESOS, Componente, combinar, componente_tecnico

RAIZ = Path(__file__).parent
VELAS = RAIZ.parent / "exp1_ingestao_binance" / "evidencias"
PASTA = RAIZ / "evidencias"
ATIVOS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

# (descrição, técnico, sentimento, ML); None = componente ausente
CENARIOS = [
    ("Tudo aponta alta com força", 0.9, 0.8, 0.8),
    ("Tudo aponta queda com força", -0.9, -0.8, -0.8),
    ("Técnico forte, sem sentimento e sem ML", 0.8, None, None),
    ("Técnico moderado, sem sentimento e sem ML", 0.5, None, None),
    ("Técnico forte, sentimento neutro", 0.9, 0.0, None),
    ("Técnico alta, sentimento levemente negativo", 0.8, -0.2, None),
    ("Técnico alta, sentimento muito negativo (divergência)", 0.8, -0.7, None),
    ("Técnico queda, sentimento muito positivo (divergência)", -0.8, 0.7, None),
    ("Técnico alta, sentimento negativo e ML a favor (divergência)", 0.8, -0.6, 0.9),
    ("Técnico neutro, sentimento e ML muito positivos", 0.0, 1.0, 1.0),
    ("Sinais fracos em todos os componentes", 0.3, 0.2, 0.25),
    ("Técnico moderado de alta, sentimento e ML de queda (divergência)", 0.5, -0.5, -0.4),
]


def cenarios() -> list[dict]:
    linhas = []
    for descricao, tec, sent, ml in CENARIOS:
        comps = [Componente(n, f, PESOS[n])
                 for n, f in (("tecnico", tec), ("sentimento", sent), ("ml", ml)) if f is not None]
        r = combinar(comps)
        linhas.append({
            "cenario": descricao,
            "forca_tecnico": tec, "forca_sentimento": sent, "forca_ml": ml,
            "pesos_usados": " / ".join(f"{c.nome} {c.peso:.2f}" for c in comps),
            "pontuacoes_S": " / ".join(f"{c.nome} {c.pontuacao:.0f}" for c in comps),
            "score_antes_da_reducao": r.divergencia["score_antes"] if r.divergencia else r.score,
            "divergencia": "sim" if r.divergencia else "não",
            "score_final": r.score, "direcao": r.direcao, "acao": r.acao,
        })
    return linhas


def dados_reais() -> dict:
    resultado = {}
    for ativo in ATIVOS:
        precos = pd.read_csv(VELAS / f"velas_{ativo}_1h.csv")["fechamento"].tolist()
        acoes, scores, rsi_extremo_e_macd_contra = Counter(), [], 0
        for i in range(MINIMO_VELAS, len(precos) + 1):
            tec = componente_tecnico(precos[i - MINIMO_VELAS:i])
            r = combinar([tec])
            acoes[r.acao] += 1
            scores.append(r.score)
            d = tec.detalhes
            if abs(d["forca_rsi"]) >= 0.5 and d["forca_rsi"] * d["forca_macd"] < -0.25:
                rsi_extremo_e_macd_contra += 1
        s = pd.Series(scores)
        resultado[ativo] = {
            "horas_avaliadas": len(scores),
            "acoes": dict(acoes),
            "score_mediano": int(s.median()),
            "score_p90": int(s.quantile(0.9)),
            "score_maximo": int(s.max()),
            "horas_com_rsi_forte_e_macd_contrario": rsi_extremo_e_macd_contra,
        }
    return resultado


def main():
    PASTA.mkdir(exist_ok=True)
    linhas = cenarios()
    with (PASTA / "cenarios_score.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)
    for l in linhas:
        print(f"{l['score_final']:>3} {l['acao']:<8} {l['divergencia']:<4} {l['cenario']}")

    reais = dados_reais()
    (PASTA / "score_dados_reais.json").write_text(
        json.dumps({"executado_em": datetime.now(UTC).isoformat(),
                    "observacao": "só o componente técnico, sem sentimento e sem ML",
                    "resultado": reais}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(reais, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
