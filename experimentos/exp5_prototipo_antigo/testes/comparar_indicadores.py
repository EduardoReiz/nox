"""Compara o RSI e o MACD do protótipo antigo com os do núcleo Python do Nox.

    backend/.venv/bin/python experimentos/exp5_prototipo_antigo/testes/comparar_indicadores.py
"""
import csv
import json
import sys
from pathlib import Path

raiz = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(raiz / "backend"))
from nox.domain.indicadores import macd, rsi  # noqa: E402

fechamentos = [float(r["fechamento"]) for r in csv.DictReader(
    open(raiz / "experimentos/exp1_ingestao_binance/evidencias/velas_BTCUSDT_1h.csv"))]
antigo = json.load(open(raiz / "experimentos/exp5_prototipo_antigo/evidencias/indicadores_antigo.json"))
novo_rsi, novo_macd = rsi(fechamentos), macd(fechamentos)


def maior_diferenca(pares):
    return round(max(abs(a - b) for a, b in pares if a is not None and b is not None), 4), len(pares)


# O antigo devolve listas mais curtas: o RSI começa na vela 15; a linha do MACD na vela 1;
# o histograma na vela 27.
rsi_pares = [(antigo["rsi"][k], novo_rsi[k + 15]) for k in range(len(antigo["rsi"]))]
linha = [(antigo["macd"][k], novo_macd.macd[k]) for k in range(len(antigo["macd"]))]
hist = [(antigo["hist"][k], novo_macd.histograma[k + 26]) for k in range(len(antigo["hist"]))]
print(f"velas: {len(fechamentos)}")
print(f"RSI, maior diferença (todas): {maior_diferenca(rsi_pares)}")
print(f"RSI, maior diferença (últimas 799): {maior_diferenca(rsi_pares[185:])}")
print(f"MACD linha, maior diferença (todas): {maior_diferenca(linha)}")
print(f"MACD linha, maior diferença (após 200 velas): {maior_diferenca(linha[200:])}")
print(f"histograma, maior diferença (todas): {maior_diferenca(hist)}")
print(f"histograma, maior diferença (após 200 velas): {maior_diferenca(hist[174:])}")
print(f"último RSI: antigo {antigo['rsi'][-1]} | novo {novo_rsi[-1]:.2f}")
print(f"último histograma: antigo {antigo['hist'][-1]} | novo {novo_macd.histograma[-1]:.8f}")
print(f"cruzamento: antigo {antigo['cruzamento']} | novo {novo_macd.cruzamento}")
