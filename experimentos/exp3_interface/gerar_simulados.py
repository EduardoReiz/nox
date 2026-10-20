"""Experimentação 3, passo 2: cinco sinais simulados, um deles com divergência.

As forças são escolhidas à mão, mas o score, a ação e o texto saem das mesmas
regras do backend, para que o simulado seja igual ao que a API entregaria.
Rodar a partir da pasta backend:

    python ../experimentos/exp3_interface/gerar_simulados.py
"""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from nox.application.sinais import para_json
from nox.domain.score import PESOS, Componente, Sinal, combinar, explicar

DESTINO = Path(__file__).parents[2] / "frontend" / "src" / "dados" / "sinais_simulados.json"
AGORA = datetime(2026, 10, 20, 15, 5, tzinfo=UTC)

# ativo, nome, preço, variação em 24 h, (força técnica, detalhes), sentimento, ML
CASOS = [
    ("BTCUSDT", "Bitcoin", 91374.0, 2.4,
     (0.85, {"rsi": 33.0, "forca_rsi": 0.7, "forca_macd": 1.0, "cruzamento": "alta"}), 0.6, 0.7),
    ("ETHUSDT", "Ethereum", 2875.1, -3.1,
     (-0.8, {"rsi": 72.0, "forca_rsi": -1.0, "forca_macd": -0.6, "cruzamento": "baixa"}), -0.5, None),
    ("SOLUSDT", "Solana", 142.37, 4.8,
     (0.8, {"rsi": 31.0, "forca_rsi": 0.9, "forca_macd": 0.7, "cruzamento": None}), -0.7, None),
    ("BNBUSDT", "BNB", 598.2, 0.2,
     (0.05, {"rsi": 52.0, "forca_rsi": 0.0, "forca_macd": 0.1, "cruzamento": None}), 0.1, None),
    ("XRPUSDT", "XRP", 0.5821, 1.1,
     (0.62, {"rsi": 45.0, "forca_rsi": 0.0, "forca_macd": 1.0, "cruzamento": "alta"}), None, None),
]


def main():
    sinais = []
    for i, (ativo, nome, preco, variacao, (f_tec, detalhes), f_sent, f_ml) in enumerate(CASOS):
        comps = [Componente("tecnico", f_tec, PESOS["tecnico"], detalhes=detalhes)]
        ausentes = []
        for nome_c, forca in (("sentimento", f_sent), ("ml", f_ml)):
            if forca is None:
                ausentes.append(nome_c)
            else:
                comps.append(Componente(nome_c, forca, PESOS[nome_c]))
        r = combinar(comps)
        gerado = AGORA - timedelta(minutes=5 * i)
        sinal = Sinal(ativo, gerado, r.acao, r.score, r.direcao, comps, ausentes, r.divergencia, "")
        sinal.explicacao = explicar(sinal)
        dados = para_json(ativo, sinal, [])
        dados["nome"] = nome
        dados["preco"] = {"ultimo": preco, "variacao_24h_pct": variacao,
                          "atualizado_em": AGORA.replace(minute=0).isoformat()}
        sinais.append(dados)
        print(f"{ativo}: {r.acao} {r.score} divergência={bool(r.divergencia)}")

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(json.dumps(sinais, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
