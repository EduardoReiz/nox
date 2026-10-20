"""Armazenamento de contas, sessões, desafios e auditoria.

Há uma versão em memória, usada nos testes, e uma no PostgreSQL, usada pela
API. As duas seguem o mesmo contrato.
"""

from copy import copy
from datetime import datetime
from typing import Protocol

import psycopg
from psycopg.rows import dict_row

from nox.domain.contas import ErroDeConta, Usuario


class RepositorioContas(Protocol):
    def criar_usuario(self, u: Usuario) -> None: ...
    def usuario_por_email(self, email: str) -> Usuario | None: ...
    def usuario_por_id(self, id_: str) -> Usuario | None: ...
    def atualizar_usuario(self, u: Usuario) -> None: ...
    def apagar_usuario(self, id_: str) -> None: ...
    def criar_sessao(self, token_hash: str, usuario_id: str, expira_em: datetime) -> None: ...
    def usuario_da_sessao(self, token_hash: str, agora: datetime) -> str | None: ...
    def apagar_sessao(self, token_hash: str) -> None: ...
    def apagar_sessoes(self, usuario_id: str) -> None: ...
    def criar_desafio(self, tipo: str, token_hash: str, usuario_id: str, expira_em: datetime) -> None: ...
    def usuario_do_desafio(self, tipo: str, token_hash: str, agora: datetime) -> str | None: ...
    def falhar_desafio(self, token_hash: str) -> int: ...
    def apagar_desafios(self, usuario_id: str, tipo: str) -> None: ...
    def registrar(self, evento: str, usuario_id: str | None, quando: datetime) -> None: ...
    def contar_eventos(self, usuario_id: str, evento: str, desde: datetime) -> int: ...
    def garantir_ativos(self, ativos: dict[str, str]) -> None: ...
    def ativos(self) -> dict[str, str]: ...
    def preferencias(self, usuario_id: str) -> list[tuple[str, bool, str | None]]: ...
    def salvar_preferencia(self, usuario_id: str, canal: str, ativa: bool, identificador_cifrado: str | None) -> None: ...
    def lista(self, usuario_id: str) -> list[tuple[str, datetime]]: ...
    def salvar_lista(self, usuario_id: str, simbolos: list[str], agora: datetime) -> None: ...


EMAIL_EM_USO = "Já existe uma conta com esse e-mail."


class ContasMemoria:
    def __init__(self):
        self.usuarios: dict[str, Usuario] = {}
        self.sessoes: dict[str, tuple[str, datetime]] = {}
        self.desafios: dict[str, dict] = {}
        self.auditoria: list[tuple[str, str | None, datetime]] = []
        self._ativos: dict[str, str] = {}
        self._preferencias: dict[str, dict[str, tuple[bool, str | None]]] = {}
        self._listas: dict[str, dict[str, datetime]] = {}

    def criar_usuario(self, u):
        if self.usuario_por_email(u.email):
            raise ErroDeConta(EMAIL_EM_USO)
        self.usuarios[u.id] = copy(u)

    def usuario_por_email(self, email):
        return next((copy(u) for u in self.usuarios.values() if u.email == email), None)

    def usuario_por_id(self, id_):
        u = self.usuarios.get(id_)
        return copy(u) if u else None

    def atualizar_usuario(self, u):
        self.usuarios[u.id] = copy(u)

    def apagar_usuario(self, id_):
        self.usuarios.pop(id_, None)
        self.apagar_sessoes(id_)
        self.desafios = {k: d for k, d in self.desafios.items() if d["usuario_id"] != id_}
        self.auditoria = [(e, None if uid == id_ else uid, q) for e, uid, q in self.auditoria]
        self._preferencias.pop(id_, None)
        self._listas.pop(id_, None)

    def criar_sessao(self, token_hash, usuario_id, expira_em):
        self.sessoes[token_hash] = (usuario_id, expira_em)

    def usuario_da_sessao(self, token_hash, agora):
        s = self.sessoes.get(token_hash)
        return s[0] if s and s[1] > agora else None

    def apagar_sessao(self, token_hash):
        self.sessoes.pop(token_hash, None)

    def apagar_sessoes(self, usuario_id):
        self.sessoes = {k: s for k, s in self.sessoes.items() if s[0] != usuario_id}

    def criar_desafio(self, tipo, token_hash, usuario_id, expira_em):
        self.desafios[token_hash] = {"tipo": tipo, "usuario_id": usuario_id,
                                     "expira_em": expira_em, "falhas": 0}

    def usuario_do_desafio(self, tipo, token_hash, agora):
        d = self.desafios.get(token_hash)
        if d and d["tipo"] == tipo and d["expira_em"] > agora:
            return d["usuario_id"]
        return None

    def falhar_desafio(self, token_hash):
        d = self.desafios.get(token_hash)
        if not d:
            return 0
        d["falhas"] += 1
        return d["falhas"]

    def apagar_desafios(self, usuario_id, tipo):
        self.desafios = {k: d for k, d in self.desafios.items()
                         if not (d["usuario_id"] == usuario_id and d["tipo"] == tipo)}

    def registrar(self, evento, usuario_id, quando):
        self.auditoria.append((evento, usuario_id, quando))

    def contar_eventos(self, usuario_id, evento, desde):
        return sum(1 for e, uid, q in self.auditoria if uid == usuario_id and e == evento and q >= desde)

    def garantir_ativos(self, ativos):
        self._ativos.update(ativos)

    def ativos(self):
        return dict(self._ativos)

    def preferencias(self, usuario_id):
        return [(c, a, i) for c, (a, i) in self._preferencias.get(usuario_id, {}).items()]

    def salvar_preferencia(self, usuario_id, canal, ativa, identificador_cifrado):
        self._preferencias.setdefault(usuario_id, {})[canal] = (ativa, identificador_cifrado)

    def lista(self, usuario_id):
        itens = self._listas.get(usuario_id, {})
        return sorted(itens.items(), key=lambda par: par[1])

    def salvar_lista(self, usuario_id, simbolos, agora):
        atual = self._listas.get(usuario_id, {})
        self._listas[usuario_id] = {s: atual.get(s, agora) for s in simbolos}


ESQUEMA = """
CREATE TABLE IF NOT EXISTS usuario (
    id                     uuid PRIMARY KEY,
    email                  text NOT NULL UNIQUE,
    nome                   text NOT NULL,
    senha_hash             text NOT NULL,
    totp_cifrado           text,
    totp_ativo             boolean NOT NULL DEFAULT false,
    totp_ultimo_passo      bigint NOT NULL DEFAULT 0,
    perfil_risco_cifrado   text,
    criado_em              timestamptz NOT NULL
);
CREATE TABLE IF NOT EXISTS sessao (
    token_hash   text PRIMARY KEY,
    usuario_id   uuid NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    expira_em    timestamptz NOT NULL
);
CREATE TABLE IF NOT EXISTS desafio (
    token_hash   text PRIMARY KEY,
    tipo         text NOT NULL CHECK (tipo IN ('2fa', 'recuperacao')),
    usuario_id   uuid NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    expira_em    timestamptz NOT NULL,
    falhas       int NOT NULL DEFAULT 0
);
-- Auditoria sem dados pessoais: só o evento, o usuário e o momento. Quando a
-- conta é excluída, o vínculo com o usuário é apagado e o evento fica anônimo.
CREATE TABLE IF NOT EXISTS auditoria (
    id           bigserial PRIMARY KEY,
    evento       text NOT NULL,
    usuario_id   uuid REFERENCES usuario(id) ON DELETE SET NULL,
    quando       timestamptz NOT NULL
);
CREATE INDEX IF NOT EXISTS auditoria_usuario ON auditoria (usuario_id, evento, quando);
ALTER TABLE usuario ADD COLUMN IF NOT EXISTS frequencia_alerta text NOT NULL DEFAULT 'cada_sinal';
-- Ativo, Lista de Acompanhamento e Preferência de Alerta (seção 18.1).
CREATE TABLE IF NOT EXISTS ativo (
    simbolo   text PRIMARY KEY,
    nome      text NOT NULL,
    tipo      text NOT NULL DEFAULT 'cripto'
);
CREATE TABLE IF NOT EXISTS lista_acompanhamento (
    usuario_id     uuid NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    simbolo        text NOT NULL REFERENCES ativo(simbolo),
    adicionado_em  timestamptz NOT NULL,
    PRIMARY KEY (usuario_id, simbolo)
);
CREATE TABLE IF NOT EXISTS preferencia_alerta (
    usuario_id              uuid NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    canal                   text NOT NULL CHECK (canal IN ('push', 'telegram')),
    identificador_cifrado   text,
    ativa                   boolean NOT NULL DEFAULT false,
    PRIMARY KEY (usuario_id, canal)
);
"""

CAMPOS = ("id", "email", "nome", "senha_hash", "totp_cifrado", "totp_ativo",
          "totp_ultimo_passo", "perfil_risco_cifrado", "frequencia_alerta", "criado_em")


class ContasPostgres:
    def __init__(self, dsn: str):
        self.con = psycopg.connect(dsn, autocommit=True, row_factory=dict_row)
        self.con.execute(ESQUEMA)

    @staticmethod
    def _usuario(linha) -> Usuario | None:
        if not linha:
            return None
        dados = {c: linha[c] for c in CAMPOS}
        dados["id"] = str(dados["id"])
        return Usuario(**dados)

    def criar_usuario(self, u):
        try:
            self.con.execute(
                f"INSERT INTO usuario ({', '.join(CAMPOS)}) VALUES ({', '.join(['%s'] * len(CAMPOS))})",
                [getattr(u, c) for c in CAMPOS])
        except psycopg.errors.UniqueViolation:
            raise ErroDeConta(EMAIL_EM_USO) from None

    def usuario_por_email(self, email):
        return self._usuario(self.con.execute("SELECT * FROM usuario WHERE email = %s", (email,)).fetchone())

    def usuario_por_id(self, id_):
        return self._usuario(self.con.execute("SELECT * FROM usuario WHERE id = %s", (id_,)).fetchone())

    def atualizar_usuario(self, u):
        campos = [c for c in CAMPOS if c not in ("id", "criado_em")]
        self.con.execute(
            f"UPDATE usuario SET {', '.join(f'{c} = %s' for c in campos)} WHERE id = %s",
            [getattr(u, c) for c in campos] + [u.id])

    def apagar_usuario(self, id_):
        self.con.execute("DELETE FROM usuario WHERE id = %s", (id_,))

    def criar_sessao(self, token_hash, usuario_id, expira_em):
        self.con.execute("INSERT INTO sessao VALUES (%s, %s, %s)", (token_hash, usuario_id, expira_em))

    def usuario_da_sessao(self, token_hash, agora):
        linha = self.con.execute("SELECT usuario_id FROM sessao WHERE token_hash = %s AND expira_em > %s",
                                 (token_hash, agora)).fetchone()
        return str(linha["usuario_id"]) if linha else None

    def apagar_sessao(self, token_hash):
        self.con.execute("DELETE FROM sessao WHERE token_hash = %s", (token_hash,))

    def apagar_sessoes(self, usuario_id):
        self.con.execute("DELETE FROM sessao WHERE usuario_id = %s", (usuario_id,))

    def criar_desafio(self, tipo, token_hash, usuario_id, expira_em):
        self.con.execute("INSERT INTO desafio (token_hash, tipo, usuario_id, expira_em) VALUES (%s, %s, %s, %s)",
                         (token_hash, tipo, usuario_id, expira_em))

    def usuario_do_desafio(self, tipo, token_hash, agora):
        linha = self.con.execute(
            "SELECT usuario_id FROM desafio WHERE token_hash = %s AND tipo = %s AND expira_em > %s",
            (token_hash, tipo, agora)).fetchone()
        return str(linha["usuario_id"]) if linha else None

    def falhar_desafio(self, token_hash):
        linha = self.con.execute("UPDATE desafio SET falhas = falhas + 1 WHERE token_hash = %s RETURNING falhas",
                                 (token_hash,)).fetchone()
        return linha["falhas"] if linha else 0

    def apagar_desafios(self, usuario_id, tipo):
        self.con.execute("DELETE FROM desafio WHERE usuario_id = %s AND tipo = %s", (usuario_id, tipo))

    def registrar(self, evento, usuario_id, quando):
        self.con.execute("INSERT INTO auditoria (evento, usuario_id, quando) VALUES (%s, %s, %s)",
                         (evento, usuario_id, quando))

    def contar_eventos(self, usuario_id, evento, desde):
        return self.con.execute(
            "SELECT count(*) AS n FROM auditoria WHERE usuario_id = %s AND evento = %s AND quando >= %s",
            (usuario_id, evento, desde)).fetchone()["n"]

    def garantir_ativos(self, ativos):
        with self.con.cursor() as cur:
            cur.executemany(
                "INSERT INTO ativo (simbolo, nome) VALUES (%s, %s) ON CONFLICT (simbolo) DO UPDATE SET nome = EXCLUDED.nome",
                list(ativos.items()))

    def ativos(self):
        return {l["simbolo"]: l["nome"] for l in self.con.execute("SELECT simbolo, nome FROM ativo ORDER BY simbolo")}

    def preferencias(self, usuario_id):
        return [(l["canal"], l["ativa"], l["identificador_cifrado"]) for l in self.con.execute(
            "SELECT canal, ativa, identificador_cifrado FROM preferencia_alerta WHERE usuario_id = %s", (usuario_id,))]

    def salvar_preferencia(self, usuario_id, canal, ativa, identificador_cifrado):
        self.con.execute("""
            INSERT INTO preferencia_alerta (usuario_id, canal, ativa, identificador_cifrado) VALUES (%s, %s, %s, %s)
            ON CONFLICT (usuario_id, canal) DO UPDATE SET ativa = EXCLUDED.ativa,
                identificador_cifrado = EXCLUDED.identificador_cifrado
        """, (usuario_id, canal, ativa, identificador_cifrado))

    def lista(self, usuario_id):
        return [(l["simbolo"], l["adicionado_em"]) for l in self.con.execute(
            "SELECT simbolo, adicionado_em FROM lista_acompanhamento WHERE usuario_id = %s ORDER BY adicionado_em, simbolo",
            (usuario_id,))]

    def salvar_lista(self, usuario_id, simbolos, agora):
        # Quem continua na lista mantém a data em que foi adicionado.
        with self.con.transaction():
            self.con.execute("DELETE FROM lista_acompanhamento WHERE usuario_id = %s AND NOT (simbolo = ANY(%s))",
                             (usuario_id, simbolos))
            with self.con.cursor() as cur:
                cur.executemany(
                    "INSERT INTO lista_acompanhamento VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                    [(usuario_id, s, agora) for s in simbolos])
