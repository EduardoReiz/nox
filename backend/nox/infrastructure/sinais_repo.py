"""Histórico de Sinais de Recomendação e registro dos alertas enviados.

O sinal guarda os componentes do score e o texto explicativo, para que a
explicação mostrada seja sempre a do cálculo que gerou a recomendação
(RNF-005). Há uma versão em memória (testes) e uma no PostgreSQL.
"""

from datetime import datetime
from typing import Protocol

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


class RepositorioSinais(Protocol):
    def ultimo(self, simbolo: str) -> dict | None: ...
    def salvar(self, sinal: dict, vela_instante: datetime) -> int | None: ...
    def registrar_alerta(self, usuario_id: str, sinal_id: int, canal: str, status: str,
                         quando: datetime, erro: str | None = None) -> None: ...
    def pendentes_resumo(self) -> dict[str, list[dict]]: ...
    def marcar_resumo_enviado(self, usuario_id: str, quando: datetime) -> None: ...
    def alertas(self, usuario_id: str) -> list[dict]: ...


class SinaisMemoria:
    def __init__(self):
        self.sinais: list[dict] = []
        self.registro: list[dict] = []

    def ultimo(self, simbolo):
        doativo = [s for s in self.sinais if s["ativo"] == simbolo]
        return doativo[-1] if doativo else None

    def salvar(self, sinal, vela_instante):
        if any(s["ativo"] == sinal["ativo"] and s["vela_instante"] == vela_instante for s in self.sinais):
            return None
        novo = {**sinal, "id": len(self.sinais) + 1, "vela_instante": vela_instante}
        self.sinais.append(novo)
        return novo["id"]

    def registrar_alerta(self, usuario_id, sinal_id, canal, status, quando, erro=None):
        self.registro.append({"usuario_id": usuario_id, "sinal_id": sinal_id, "canal": canal,
                              "status": status, "quando": quando, "erro": erro})

    def pendentes_resumo(self):
        por_usuario: dict[str, list[dict]] = {}
        for a in self.registro:
            if a["canal"] == "resumo" and a["status"] == "pendente":
                sinal = next(s for s in self.sinais if s["id"] == a["sinal_id"])
                por_usuario.setdefault(a["usuario_id"], []).append(sinal)
        return por_usuario

    def marcar_resumo_enviado(self, usuario_id, quando):
        for a in self.registro:
            if a["usuario_id"] == usuario_id and a["canal"] == "resumo" and a["status"] == "pendente":
                a["status"], a["quando"] = "enviado", quando

    def alertas(self, usuario_id):
        return [a for a in self.registro if a["usuario_id"] == usuario_id]


ESQUEMA = """
CREATE TABLE IF NOT EXISTS sinal (
    id             bigserial PRIMARY KEY,
    simbolo        text NOT NULL REFERENCES ativo(simbolo),
    vela_instante  timestamptz NOT NULL,
    gerado_em      timestamptz NOT NULL,
    acao           text NOT NULL CHECK (acao IN ('comprar', 'vender', 'manter')),
    score          int NOT NULL CHECK (score BETWEEN 0 AND 100),
    direcao        text NOT NULL,
    componentes    jsonb NOT NULL,
    divergencia    jsonb,
    explicacao     text NOT NULL,
    UNIQUE (simbolo, vela_instante)
);
CREATE TABLE IF NOT EXISTS alerta (
    id          bigserial PRIMARY KEY,
    usuario_id  uuid NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    sinal_id    bigint NOT NULL REFERENCES sinal(id),
    canal       text NOT NULL CHECK (canal IN ('push', 'telegram', 'resumo')),
    status      text NOT NULL CHECK (status IN ('enviado', 'falhou', 'pendente')),
    quando      timestamptz NOT NULL,
    erro        text
);
CREATE INDEX IF NOT EXISTS alerta_pendente ON alerta (canal, status);
"""


class SinaisPostgres:
    def __init__(self, dsn: str):
        self.con = psycopg.connect(dsn, autocommit=True, row_factory=dict_row)
        self.con.execute(ESQUEMA)

    @staticmethod
    def _sinal(l) -> dict:
        return {"id": l["id"], "ativo": l["simbolo"], "vela_instante": l["vela_instante"],
                "gerado_em": l["gerado_em"].isoformat(), "acao": l["acao"], "score": l["score"],
                "direcao": l["direcao"], "componentes": l["componentes"], "divergencia": l["divergencia"],
                "explicacao": l["explicacao"]}

    def ultimo(self, simbolo):
        l = self.con.execute("SELECT * FROM sinal WHERE simbolo = %s ORDER BY vela_instante DESC LIMIT 1",
                             (simbolo,)).fetchone()
        return self._sinal(l) if l else None

    def salvar(self, sinal, vela_instante):
        l = self.con.execute("""
            INSERT INTO sinal (simbolo, vela_instante, gerado_em, acao, score, direcao, componentes,
                               divergencia, explicacao)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (simbolo, vela_instante) DO NOTHING RETURNING id
        """, (sinal["ativo"], vela_instante, sinal["gerado_em"], sinal["acao"], sinal["score"], sinal["direcao"],
              Jsonb(sinal["componentes"]), Jsonb(sinal["divergencia"]) if sinal["divergencia"] else None,
              sinal["explicacao"])).fetchone()
        return l["id"] if l else None

    def registrar_alerta(self, usuario_id, sinal_id, canal, status, quando, erro=None):
        self.con.execute("INSERT INTO alerta (usuario_id, sinal_id, canal, status, quando, erro) "
                         "VALUES (%s, %s, %s, %s, %s, %s)", (usuario_id, sinal_id, canal, status, quando, erro))

    def pendentes_resumo(self):
        por_usuario: dict[str, list[dict]] = {}
        for l in self.con.execute("""
            SELECT a.usuario_id, s.* FROM alerta a JOIN sinal s ON s.id = a.sinal_id
            WHERE a.canal = 'resumo' AND a.status = 'pendente' ORDER BY a.quando
        """):
            por_usuario.setdefault(str(l["usuario_id"]), []).append(self._sinal(l))
        return por_usuario

    def marcar_resumo_enviado(self, usuario_id, quando):
        self.con.execute("UPDATE alerta SET status = 'enviado', quando = %s "
                         "WHERE usuario_id = %s AND canal = 'resumo' AND status = 'pendente'", (quando, usuario_id))

    def alertas(self, usuario_id):
        return list(self.con.execute("SELECT * FROM alerta WHERE usuario_id = %s ORDER BY id", (usuario_id,)))

