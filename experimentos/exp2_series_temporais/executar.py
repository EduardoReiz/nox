"""Experimentação 2 – Organização e consulta de séries temporais: InfluxDB x PostgreSQL.

Pré-requisito: `docker compose up -d` na raiz do projeto. Rodar a partir da
pasta backend, com o ambiente ativado:

    python ../experimentos/exp2_series_temporais/executar.py
"""

import csv
import json
import logging
import statistics
import subprocess
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

from nox.domain.mercado import Vela
from nox.infrastructure import config
from nox.infrastructure.binance import ClienteBinance
from nox.infrastructure.series import SeriesInflux, SeriesPostgres

PASTA = Path(__file__).parent / "evidencias"
VELAS_EXP1 = Path(__file__).parent.parent / "exp1_ingestao_binance" / "evidencias"
ATIVOS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
REPETICOES = 30
DIA = datetime(2026, 10, 1, tzinfo=UTC)
MES = (datetime(2026, 9, 1, tzinfo=UTC), datetime(2026, 10, 1, tzinfo=UTC))
ATIVO_TESTE = "LACUNATESTE"


def ler_csv(ativo: str) -> list[Vela]:
    with (VELAS_EXP1 / f"velas_{ativo}_1h.csv").open(encoding="utf-8") as f:
        return [Vela(l["ativo"], l["intervalo"], datetime.fromisoformat(l["instante"]),
                     float(l["abertura"]), float(l["maxima"]), float(l["minima"]),
                     float(l["fechamento"]), float(l["volume"]), l["fonte"])
                for l in csv.DictReader(f)]


def medir(funcao, repeticoes: int = REPETICOES) -> tuple[float, object]:
    """Mediana do tempo em milissegundos, depois de uma execução de aquecimento."""
    resultado = funcao()
    tempos = []
    for _ in range(repeticoes):
        t = time.perf_counter()
        funcao()
        tempos.append((time.perf_counter() - t) * 1000)
    return round(statistics.median(tempos), 2), resultado


def tamanho_influx() -> int | None:
    try:
        saida = subprocess.run(
            ["docker", "compose", "exec", "-T", "influxdb", "du", "-sk", "/var/lib/influxdb2/engine"],
            capture_output=True, text=True, check=True, cwd=Path(__file__).parents[2]).stdout
        return int(saida.split()[0]) * 1024
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
        return None


def teste_de_escala(pg: SeriesPostgres, ifx: SeriesInflux, dias: int = 90) -> dict:
    """O caso que motiva o InfluxDB: muitos meses de velas de 1 minuto. Aqui,
    90 dias do BTC (cerca de 130 mil velas), com as mesmas quatro perguntas."""
    fim = datetime.now(UTC).replace(second=0, microsecond=0)
    inicio = fim - timedelta(days=dias)
    t = time.perf_counter()
    velas = ClienteBinance().historico("BTCUSDT", "1m", inicio)
    logging.info("escala: %d velas de 1m coletadas em %.0fs", len(velas), time.perf_counter() - t)

    dia = (fim - timedelta(days=10)).replace(hour=0, minute=0)
    mes = (fim - timedelta(days=40), fim - timedelta(days=10))
    saida = {"dias": dias, "velas": len(velas), "bancos": {}}
    for nome, banco in {"PostgreSQL": pg, "InfluxDB": ifx}.items():
        t = time.perf_counter()
        banco.gravar(velas)
        escrita = time.perf_counter() - t
        t1, ultimas = medir(lambda: banco.ultimas("BTCUSDT", "1m", 200), 10)
        t2, do_dia = medir(lambda: banco.periodo("BTCUSDT", "1m", dia, dia + timedelta(days=1)), 10)
        t3, medias = medir(lambda: banco.media_diaria("BTCUSDT", "1m", *mes), 10)
        t4, lacunas = medir(lambda: banco.lacunas("BTCUSDT", "1m", inicio, fim), 10)
        saida["bancos"][nome] = {
            "escrita_s": round(escrita, 1),
            "velas_por_segundo": round(len(velas) / escrita),
            "consultas_ms_mediana": {"ultimas_200_velas": t1, "velas_de_um_dia": t2,
                                     "media_por_dia_de_um_mes": t3, "lacunas_90_dias": t4},
            "conferencia": {"ultimas": len(ultimas), "velas_do_dia": len(do_dia),
                            "dias": len(medias),
                            "lacunas": [[a.isoformat(), b.isoformat()] for a, b in lacunas]},
        }
        logging.info("escala %s: %s", nome, saida["bancos"][nome]["consultas_ms_mediana"])
    saida["mesmos_resultados"] = (saida["bancos"]["PostgreSQL"]["conferencia"]
                                  == saida["bancos"]["InfluxDB"]["conferencia"])
    saida["armazenamento_bytes"] = {"PostgreSQL": pg.tamanho_bytes(),
                                    "InfluxDB_engine": tamanho_influx()}
    return saida


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    PASTA.mkdir(exist_ok=True)

    # Passo 2: o mesmo conjunto de velas nos dois bancos. Às velas da
    # Experimentação 1 soma-se o histórico do BTC desde janeiro.
    velas = {a: ler_csv(a) for a in ATIVOS}
    historico = ClienteBinance().historico("BTCUSDT", "1h", datetime(2026, 1, 1, tzinfo=UTC))
    por_instante = {v.instante: v for v in historico + velas["BTCUSDT"]}
    velas["BTCUSDT"] = [por_instante[t] for t in sorted(por_instante)]
    total = sum(len(v) for v in velas.values())
    logging.info("velas a gravar: %d", total)

    # Série de teste com lacunas conhecidas: tira a vela 100 e as velas 300 e 301.
    base = velas["ETHUSDT"]
    com_lacunas = [Vela(ATIVO_TESTE, *list(vars(v).values())[1:]) for i, v in enumerate(base)
                   if i not in (100, 300, 301)]
    lacunas_esperadas = [(base[99].instante, base[101].instante),
                         (base[299].instante, base[302].instante)]

    pg = SeriesPostgres(config.postgres_dsn())
    ifx = SeriesInflux(**config.influx())
    bancos = {"PostgreSQL": pg, "InfluxDB": ifx}
    resultado = {"executado_em": datetime.now(UTC).isoformat(), "velas_gravadas": total,
                 "repeticoes_por_consulta": REPETICOES, "bancos": {}}

    for nome, banco in bancos.items():
        for a in ATIVOS + [ATIVO_TESTE]:
            banco.apagar(a)
        t = time.perf_counter()
        for serie in velas.values():
            banco.gravar(serie)
        tempo_escrita = time.perf_counter() - t
        banco.gravar(com_lacunas)

        # Unicidade: gravar de novo a mesma vela com outro preço.
        original = velas["SOLUSDT"][-1]
        alterada = Vela(*list(vars(original).values())[:6], 999.0, original.volume, original.fonte)
        banco.gravar([alterada])
        mesma_hora = banco.periodo("SOLUSDT", "1h", original.instante,
                                   original.instante + timedelta(hours=1))
        banco.gravar([original])

        # Passo 3: as quatro consultas.
        fim_mes_lacunas = base[-1].instante + timedelta(hours=1)
        t1, ultimas = medir(lambda: banco.ultimas("BTCUSDT", "1h", 200))
        t2, dia = medir(lambda: banco.periodo("BTCUSDT", "1h", DIA, DIA + timedelta(days=1)))
        t3, medias = medir(lambda: banco.media_diaria("BTCUSDT", "1h", *MES))
        t4, lacunas = medir(lambda: banco.lacunas(ATIVO_TESTE, "1h", base[0].instante,
                                                  fim_mes_lacunas))
        t5, lacunas_reais = medir(lambda: banco.lacunas("BTCUSDT", "1h", historico[0].instante,
                                                        velas["BTCUSDT"][-1].instante + timedelta(hours=1)))

        resultado["bancos"][nome] = {
            "escrita": {"velas": total, "segundos": round(tempo_escrita, 2),
                        "velas_por_segundo": round(total / tempo_escrita)},
            "unicidade": {"registros_na_mesma_hora_apos_regravar": len(mesma_hora),
                          "fechamento_que_ficou": mesma_hora[0].fechamento if mesma_hora else None},
            "consultas_ms_mediana": {
                "ultimas_200_velas": t1, "velas_de_um_dia": t2,
                "media_por_dia_de_um_mes": t3, "lacunas_serie_teste": t4,
                "lacunas_historico_btc": t5,
            },
            "conferencia": {
                "ultimas_200": len(ultimas),
                "ultima_vela": ultimas[-1].instante.isoformat(),
                "velas_do_dia": len(dia),
                "dias_no_mes": len(medias),
                "media_primeiro_dia": round(medias[0][1], 2) if medias else None,
                "lacunas_encontradas_teste": [[a.isoformat(), b.isoformat()] for a, b in lacunas],
                "lacunas_corretas": sorted(lacunas) == sorted(lacunas_esperadas),
                "lacunas_historico_btc": [[a.isoformat(), b.isoformat()] for a, b in lacunas_reais],
            },
        }
        logging.info("%s: %s", nome, json.dumps(resultado["bancos"][nome]["consultas_ms_mediana"]))

    # As duas implementações precisam devolver os mesmos números.
    a, b = resultado["bancos"]["PostgreSQL"], resultado["bancos"]["InfluxDB"]
    resultado["mesmos_resultados_nos_dois_bancos"] = a["conferencia"] == b["conferencia"]
    medias_pg = pg.media_diaria("BTCUSDT", "1h", *MES)
    medias_ifx = ifx.media_diaria("BTCUSDT", "1h", *MES)
    resultado["maior_diferenca_media_diaria"] = max(
        abs(x[1] - y[1]) for x, y in zip(medias_pg, medias_ifx))
    resultado["datas_media_diaria_iguais"] = [d for d, _ in medias_pg] == [d for d, _ in medias_ifx]

    resultado["armazenamento_bytes"] = {"PostgreSQL": pg.tamanho_bytes(),
                                        "InfluxDB_engine": tamanho_influx()}

    resultado["escala_1m"] = teste_de_escala(pg, ifx)

    (PASTA / "resumo.json").write_text(json.dumps(resultado, indent=2, ensure_ascii=False),
                                       encoding="utf-8")
    pg.fechar()
    ifx.fechar()
    print(json.dumps(resultado, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
