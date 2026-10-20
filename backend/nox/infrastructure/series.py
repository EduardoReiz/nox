"""Acesso às séries de observações de mercado (RF-002, seção 18.2).

Há uma implementação para o PostgreSQL e outra para o InfluxDB, com as
mesmas operações, para que a Experimentação 2 compare as duas com as mesmas
perguntas e o resto do sistema não precise saber qual banco está em uso.
"""

from datetime import UTC, date, datetime, timedelta
from typing import Protocol

import psycopg
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

from nox.domain.mercado import INTERVALOS, Vela

MEDICAO = "observacao_mercado"


class RepositorioSeries(Protocol):
    def gravar(self, velas: list[Vela]) -> None: ...
    def ultimas(self, ativo: str, intervalo: str, quantidade: int) -> list[Vela]: ...
    def periodo(self, ativo: str, intervalo: str, inicio: datetime, fim: datetime) -> list[Vela]: ...
    def media_diaria(self, ativo: str, intervalo: str, inicio: datetime,
                     fim: datetime) -> list[tuple[date, float]]: ...
    def lacunas(self, ativo: str, intervalo: str, inicio: datetime,
                fim: datetime) -> list[tuple[datetime, datetime]]: ...


# --- PostgreSQL ----------------------------------------------------------------

ESQUEMA_PG = """
CREATE TABLE IF NOT EXISTS observacao_mercado (
    ativo       text             NOT NULL,
    intervalo   text             NOT NULL,
    instante    timestamptz      NOT NULL,
    abertura    double precision NOT NULL,
    maxima      double precision NOT NULL,
    minima      double precision NOT NULL,
    fechamento  double precision NOT NULL,
    volume      double precision NOT NULL,
    fonte       text             NOT NULL,
    -- Unicidade de cada observação: ativo, intervalo e instante.
    PRIMARY KEY (ativo, intervalo, instante)
);
"""

COLUNAS = "ativo, intervalo, instante, abertura, maxima, minima, fechamento, volume, fonte"


class SeriesPostgres:
    def __init__(self, dsn: str):
        self.con = psycopg.connect(dsn, autocommit=True)
        self.con.execute(ESQUEMA_PG)

    def gravar(self, velas: list[Vela]) -> None:
        # Gravar de novo a mesma vela substitui a anterior, em vez de duplicar.
        sql = f"""
            INSERT INTO observacao_mercado ({COLUNAS})
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (ativo, intervalo, instante) DO UPDATE SET
                abertura = EXCLUDED.abertura, maxima = EXCLUDED.maxima,
                minima = EXCLUDED.minima, fechamento = EXCLUDED.fechamento,
                volume = EXCLUDED.volume, fonte = EXCLUDED.fonte
        """
        with self.con.cursor() as cur:
            cur.executemany(sql, [(v.ativo, v.intervalo, v.instante, v.abertura, v.maxima,
                                   v.minima, v.fechamento, v.volume, v.fonte) for v in velas])

    @staticmethod
    def _velas(linhas) -> list[Vela]:
        return [Vela(*linha) for linha in linhas]

    def ultimas(self, ativo, intervalo, quantidade):
        linhas = self.con.execute(f"""
            SELECT {COLUNAS} FROM observacao_mercado
            WHERE ativo = %s AND intervalo = %s
            ORDER BY instante DESC LIMIT %s
        """, (ativo, intervalo, quantidade)).fetchall()
        return self._velas(reversed(linhas))

    def periodo(self, ativo, intervalo, inicio, fim):
        return self._velas(self.con.execute(f"""
            SELECT {COLUNAS} FROM observacao_mercado
            WHERE ativo = %s AND intervalo = %s AND instante >= %s AND instante < %s
            ORDER BY instante
        """, (ativo, intervalo, inicio, fim)).fetchall())

    def media_diaria(self, ativo, intervalo, inicio, fim):
        linhas = self.con.execute("""
            SELECT (date_trunc('day', instante AT TIME ZONE 'UTC'))::date AS dia, avg(fechamento)
            FROM observacao_mercado
            WHERE ativo = %s AND intervalo = %s AND instante >= %s AND instante < %s
            GROUP BY dia ORDER BY dia
        """, (ativo, intervalo, inicio, fim)).fetchall()
        return [(dia, float(media)) for dia, media in linhas]

    def lacunas(self, ativo, intervalo, inicio, fim):
        return [(a, b) for a, b in self.con.execute("""
            SELECT instante, proximo FROM (
                SELECT instante, lead(instante) OVER (ORDER BY instante) AS proximo
                FROM observacao_mercado
                WHERE ativo = %s AND intervalo = %s AND instante >= %s AND instante < %s
            ) t
            WHERE proximo - instante > %s
        """, (ativo, intervalo, inicio, fim, INTERVALOS[intervalo])).fetchall()]

    def apagar(self, ativo: str) -> None:
        self.con.execute("DELETE FROM observacao_mercado WHERE ativo = %s", (ativo,))

    def tamanho_bytes(self) -> int:
        return self.con.execute(
            "SELECT pg_total_relation_size('observacao_mercado')").fetchone()[0]

    def fechar(self):
        self.con.close()


# --- InfluxDB --------------------------------------------------------------------


def _rfc(instante: datetime) -> str:
    return instante.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


class SeriesInflux:
    """No InfluxDB cada vela é um ponto da medição observacao_mercado. Ativo,
    intervalo e fonte são tags (indexadas); os preços e o volume são campos.
    Ponto com as mesmas tags e o mesmo instante substitui o anterior."""

    def __init__(self, url: str, token: str, org: str, bucket: str):
        self.cliente = InfluxDBClient(url=url, token=token, org=org, timeout=30_000)
        self.escrita = self.cliente.write_api(write_options=SYNCHRONOUS)
        self.consulta = self.cliente.query_api()
        self.org, self.bucket = org, bucket

    def gravar(self, velas: list[Vela]) -> None:
        pontos = [
            Point(MEDICAO)
            .tag("ativo", v.ativo).tag("intervalo", v.intervalo).tag("fonte", v.fonte)
            .field("abertura", v.abertura).field("maxima", v.maxima).field("minima", v.minima)
            .field("fechamento", v.fechamento).field("volume", v.volume)
            .time(v.instante, WritePrecision.S)
            for v in velas
        ]
        for i in range(0, len(pontos), 5000):
            self.escrita.write(self.bucket, self.org, pontos[i:i + 5000])

    def _filtro(self, ativo, intervalo, inicio="0", fim="now()") -> str:
        return f"""
            from(bucket: "{self.bucket}")
              |> range(start: {inicio}, stop: {fim})
              |> filter(fn: (r) => r._measurement == "{MEDICAO}")
              |> filter(fn: (r) => r.ativo == "{ativo}" and r.intervalo == "{intervalo}")
        """

    def _velas(self, flux: str) -> list[Vela]:
        velas = []
        for tabela in self.consulta.query(flux, org=self.org):
            for r in tabela.records:
                velas.append(Vela(r["ativo"], r["intervalo"], r.get_time(), r["abertura"],
                                  r["maxima"], r["minima"], r["fechamento"], r["volume"],
                                  r["fonte"]))
        return velas

    PIVOT = '|> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")'

    def ultimas(self, ativo, intervalo, quantidade):
        # O tail corta cada campo antes do pivot. Fazer o pivot da série inteira
        # e só depois ordenar e limitar deixava a consulta 3,5 vezes mais lenta.
        return self._velas(self._filtro(ativo, intervalo) + f"""
              |> tail(n: {quantidade})
              {self.PIVOT}
              |> group()
              |> sort(columns: ["_time"])
        """)

    def periodo(self, ativo, intervalo, inicio, fim):
        return self._velas(self._filtro(ativo, intervalo, _rfc(inicio), _rfc(fim)) + f"""
              {self.PIVOT}
              |> group()
              |> sort(columns: ["_time"])
        """)

    def media_diaria(self, ativo, intervalo, inicio, fim):
        flux = self._filtro(ativo, intervalo, _rfc(inicio), _rfc(fim)) + """
              |> filter(fn: (r) => r._field == "fechamento")
              |> aggregateWindow(every: 1d, fn: mean, createEmpty: false, timeSrc: "_start")
        """
        resultado = []
        for tabela in self.consulta.query(flux, org=self.org):
            for r in tabela.records:
                resultado.append((r.get_time().date(), float(r.get_value())))
        return resultado

    def lacunas(self, ativo, intervalo, inicio, fim):
        passo = int(INTERVALOS[intervalo].total_seconds())
        flux = self._filtro(ativo, intervalo, _rfc(inicio), _rfc(fim)) + f"""
              |> filter(fn: (r) => r._field == "fechamento")
              |> elapsed(unit: 1s)
              |> filter(fn: (r) => r.elapsed > {passo})
        """
        resultado = []
        for tabela in self.consulta.query(flux, org=self.org):
            for r in tabela.records:
                fim_lacuna = r.get_time()
                resultado.append((fim_lacuna - timedelta(seconds=r["elapsed"]), fim_lacuna))
        return resultado

    def apagar(self, ativo: str) -> None:
        self.cliente.delete_api().delete(
            "1970-01-01T00:00:00Z", "2100-01-01T00:00:00Z",
            f'_measurement="{MEDICAO}" AND ativo="{ativo}"', bucket=self.bucket, org=self.org)

    def fechar(self):
        self.cliente.close()
