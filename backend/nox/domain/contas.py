"""Regras de conta do usuário (RF-010, RNE-005, RNF-003).

Coleta mínima (seção 18.2): nome, e-mail e senha. Sem CPF, endereço ou saldo.
"""

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime

SENHA_MINIMA = 10
SENHA_MAXIMA = 128  # limite para o hash não virar porta de ataque de negação de serviço
NOME_MAXIMO = 80

# Algumas das senhas mais vazadas. A regra de tamanho já barra a maioria;
# esta lista pega as que passam dos 10 caracteres.
SENHAS_COMUNS = {
    "1234567890", "12345678910", "123456789a", "qwertyuiop", "1q2w3e4r5t", "senha12345",
    "senha123456", "password123", "passw0rd123", "abcdefghij", "0123456789", "1111111111",
    "aaaaaaaaaa", "iloveyou123", "brasil12345", "flamengo123", "corinthians", "palmeiras123",
}

EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ErroDeConta(ValueError):
    """Erro que pode ser mostrado ao usuário como está."""


@dataclass
class Usuario:
    email: str
    nome: str
    senha_hash: str
    criado_em: datetime
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    totp_cifrado: str | None = None  # segredo do 2FA, cifrado (RNE-005)
    totp_ativo: bool = False
    totp_ultimo_passo: int = 0  # impede reusar o mesmo código
    perfil_risco_cifrado: str | None = None  # RF-011, cifrado (RNE-005)
    frequencia_alerta: str = "cada_sinal"  # RF-011 e RF-012


def normalizar_email(email: str) -> str:
    email = email.strip().lower()
    if len(email) > 254 or not EMAIL.match(email):
        raise ErroDeConta("Digite um e-mail válido.")
    return email


def validar_nome(nome: str) -> str:
    nome = " ".join(nome.split())
    if not nome:
        raise ErroDeConta("Digite seu nome.")
    if len(nome) > NOME_MAXIMO:
        raise ErroDeConta(f"O nome pode ter até {NOME_MAXIMO} caracteres.")
    return nome


def validar_senha(senha: str, email: str = "") -> None:
    if len(senha) < SENHA_MINIMA:
        raise ErroDeConta(f"A senha precisa ter pelo menos {SENHA_MINIMA} caracteres.")
    if len(senha) > SENHA_MAXIMA:
        raise ErroDeConta(f"A senha pode ter até {SENHA_MAXIMA} caracteres.")
    if senha.lower() in SENHAS_COMUNS or len(set(senha)) < 4:
        raise ErroDeConta("Essa senha é fácil de adivinhar. Escolha outra.")
    usuario_email = email.split("@")[0].lower()
    if len(usuario_email) >= 4 and usuario_email in senha.lower():
        raise ErroDeConta("A senha não pode conter o seu e-mail.")


# --- perfil e preferências (RF-011) ------------------------------------------

PERFIS = {
    "conservador": "Prefiro perder pouco, mesmo ganhando menos. Uma queda forte me tiraria o sono.",
    "moderado": "Aceito algumas quedas no caminho se, no longo prazo, puder ganhar mais.",
    "arrojado": "Aguento grandes oscilações e sei que posso perder boa parte do que investi.",
}
FREQUENCIAS = {"cada_sinal": "A cada sinal novo", "resumo_diario": "Um resumo por dia"}
CANAIS = ("push", "telegram")
TELEGRAM = re.compile(r"^@?[A-Za-z][A-Za-z0-9_]{4,31}$")
MAX_LISTA = 20


def validar_perfil(perfil: str | None) -> str | None:
    if perfil is not None and perfil not in PERFIS:
        raise ErroDeConta("Escolha um dos perfis: conservador, moderado ou arrojado.")
    return perfil


def validar_frequencia(frequencia: str) -> str:
    if frequencia not in FREQUENCIAS:
        raise ErroDeConta("Escolha a frequência dos alertas.")
    return frequencia


def normalizar_telegram(usuario: str) -> str:
    """Nome de usuário do Telegram: 5 a 32 letras, números ou _, começando por letra."""
    usuario = usuario.strip()
    if not TELEGRAM.match(usuario):
        raise ErroDeConta("Digite seu usuário do Telegram, por exemplo @maria_silva.")
    return "@" + usuario.lstrip("@")


@dataclass
class PreferenciaAlerta:
    canal: str  # "push" ou "telegram"
    ativa: bool
    identificador: str | None = None  # usuário do Telegram; no push, a inscrição do navegador (RF-012)
