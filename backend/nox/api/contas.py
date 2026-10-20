"""Rotas de conta (RF-010).

A sessão fica num cookie httpOnly: o JavaScript da página não consegue lê-lo,
o que protege contra roubo de sessão por script injetado. SameSite=Strict
impede que outro site faça pedidos usando a sessão do usuário.
"""

import os
from functools import lru_cache

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from nox.application.autenticacao import ServicoAutenticacao
from nox.application.perfil import ServicoPerfil
from nox.application.sinais import ATIVOS
from nox.domain.contas import ErroDeConta, Usuario
from nox.infrastructure import config
from nox.infrastructure.contas_repo import ContasPostgres
from nox.infrastructure.email import EmailNoLog
from nox.infrastructure.seguranca import Cifra

COOKIE = "nox_sessao"
rotas = APIRouter(prefix="/api/conta", tags=["conta"])


@lru_cache
def _repo() -> ContasPostgres:
    return ContasPostgres(config.postgres_dsn())


@lru_cache
def _cifra() -> Cifra:
    return Cifra(config.chave_dados())


@lru_cache
def servico() -> ServicoAutenticacao:
    return ServicoAutenticacao(_repo(), _cifra(), EmailNoLog(),
                               url_app=os.environ.get("NOX_URL_APP", "http://localhost:5173"))


@lru_cache
def servico_perfil() -> ServicoPerfil:
    return ServicoPerfil(_repo(), _cifra(), ATIVOS)


def _abrir(resposta: Response, token: str) -> None:
    resposta.set_cookie(COOKIE, token, httponly=True, samesite="strict", secure=config.cookie_seguro(),
                        max_age=7 * 24 * 3600, path="/api")


def _erro(e: ErroDeConta) -> HTTPException:
    return HTTPException(400, str(e))


def usuario_atual(nox_sessao: str | None = Cookie(None),
                  s: ServicoAutenticacao = Depends(servico)) -> Usuario:
    u = s.usuario_da_sessao(nox_sessao)
    if u is None:
        raise HTTPException(401, "Entre na sua conta para continuar.")
    return u


def publico(u: Usuario) -> dict:
    """Só o que a tela precisa. Hash da senha e segredo do 2FA nunca saem."""
    return {"nome": u.nome, "email": u.email, "dois_fatores": u.totp_ativo,
            "criado_em": u.criado_em.isoformat()}


class Cadastro(BaseModel):
    nome: str
    email: str
    senha: str


class Login(BaseModel):
    email: str
    senha: str


class Codigo(BaseModel):
    desafio: str
    codigo: str


class SoCodigo(BaseModel):
    codigo: str


class SoSenha(BaseModel):
    senha: str


class SoEmail(BaseModel):
    email: str


class NovaSenha(BaseModel):
    token: str
    senha: str


class Preferencias(BaseModel):
    perfil_risco: str | None = None
    frequencia: str = "cada_sinal"
    canais: dict[str, dict] = {}


class Lista(BaseModel):
    ativos: list[str]


@rotas.post("/cadastro", status_code=201)
def cadastrar(dados: Cadastro, resposta: Response, s: ServicoAutenticacao = Depends(servico)):
    try:
        token = s.cadastrar(dados.nome, dados.email, dados.senha)
    except ErroDeConta as e:
        raise _erro(e) from None
    _abrir(resposta, token)
    return publico(s.usuario_da_sessao(token))


@rotas.post("/entrar")
def entrar(dados: Login, resposta: Response, s: ServicoAutenticacao = Depends(servico)):
    try:
        r = s.entrar(dados.email, dados.senha)
    except ErroDeConta as e:
        raise _erro(e) from None
    if r.desafio_2fa:
        return {"precisa_codigo": True, "desafio": r.desafio_2fa}
    _abrir(resposta, r.sessao)
    return {"precisa_codigo": False, "usuario": publico(s.usuario_da_sessao(r.sessao))}


@rotas.post("/entrar/codigo")
def confirmar_codigo(dados: Codigo, resposta: Response, s: ServicoAutenticacao = Depends(servico)):
    try:
        token = s.confirmar_codigo(dados.desafio, dados.codigo)
    except ErroDeConta as e:
        raise _erro(e) from None
    _abrir(resposta, token)
    return publico(s.usuario_da_sessao(token))


@rotas.post("/sair", status_code=204)
def sair(resposta: Response, nox_sessao: str | None = Cookie(None), s: ServicoAutenticacao = Depends(servico)):
    if nox_sessao:
        s.sair(nox_sessao)
    resposta.delete_cookie(COOKIE, path="/api")


@rotas.get("/eu")
def eu(u: Usuario = Depends(usuario_atual)):
    return publico(u)


@rotas.post("/2fa/iniciar")
def iniciar_2fa(u: Usuario = Depends(usuario_atual), s: ServicoAutenticacao = Depends(servico)):
    try:
        return s.iniciar_2fa(u)
    except ErroDeConta as e:
        raise _erro(e) from None


@rotas.post("/2fa/ativar")
def ativar_2fa(dados: SoCodigo, u: Usuario = Depends(usuario_atual), s: ServicoAutenticacao = Depends(servico)):
    try:
        s.ativar_2fa(u, dados.codigo)
    except ErroDeConta as e:
        raise _erro(e) from None
    return {"dois_fatores": True}


@rotas.post("/2fa/desativar")
def desativar_2fa(dados: SoSenha, u: Usuario = Depends(usuario_atual), s: ServicoAutenticacao = Depends(servico)):
    try:
        s.desativar_2fa(u, dados.senha)
    except ErroDeConta as e:
        raise _erro(e) from None
    return {"dois_fatores": False}


@rotas.post("/senha/esqueci", status_code=202)
def esqueci(dados: SoEmail, s: ServicoAutenticacao = Depends(servico)):
    s.pedir_recuperacao(dados.email)
    return {"mensagem": "Se houver uma conta com esse e-mail, enviamos um link para criar uma senha nova."}


@rotas.post("/senha/redefinir")
def redefinir(dados: NovaSenha, s: ServicoAutenticacao = Depends(servico)):
    try:
        s.redefinir_senha(dados.token, dados.senha)
    except ErroDeConta as e:
        raise _erro(e) from None
    return {"mensagem": "Senha alterada. Entre com a senha nova."}


@rotas.post("/excluir", status_code=204)
def excluir(dados: SoSenha, resposta: Response, u: Usuario = Depends(usuario_atual),
            s: ServicoAutenticacao = Depends(servico)):
    try:
        s.excluir_conta(u, dados.senha)
    except ErroDeConta as e:
        raise _erro(e) from None
    resposta.delete_cookie(COOKIE, path="/api")


# --- perfil, alertas e lista de ativos (RF-011, RF-015) ------------------------


@rotas.get("/preferencias")
def ler_preferencias(u: Usuario = Depends(usuario_atual), p: ServicoPerfil = Depends(servico_perfil)):
    return p.preferencias(u)


@rotas.put("/preferencias")
def salvar_preferencias(dados: Preferencias, u: Usuario = Depends(usuario_atual),
                        p: ServicoPerfil = Depends(servico_perfil)):
    try:
        return p.salvar_preferencias(u, dados.perfil_risco, dados.frequencia, dados.canais)
    except ErroDeConta as e:
        raise _erro(e) from None


@rotas.get("/lista")
def ler_lista(u: Usuario = Depends(usuario_atual), p: ServicoPerfil = Depends(servico_perfil)):
    return {"ativos": p.lista(u)}


@rotas.put("/lista")
def salvar_lista(dados: Lista, u: Usuario = Depends(usuario_atual), p: ServicoPerfil = Depends(servico_perfil)):
    try:
        return {"ativos": p.salvar_lista(u, dados.ativos)}
    except ErroDeConta as e:
        raise _erro(e) from None


@rotas.get("/meus-dados")
def meus_dados(u: Usuario = Depends(usuario_atual), p: ServicoPerfil = Depends(servico_perfil)):
    """LGPD: o titular baixa tudo o que o Nox guarda sobre ele."""
    return JSONResponse(p.meus_dados(u),
                        headers={"Content-Disposition": 'attachment; filename="meus-dados-nox.json"'})
