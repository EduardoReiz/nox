"""Primitivas de segurança: hash de senha, cifra de dados pessoais, tokens e TOTP."""

import hashlib
import hmac
import secrets

import pyotp
import segno
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from cryptography.fernet import Fernet, InvalidToken


class Senhas:
    """Argon2id (RNF-003). Os parâmetros padrão usam 64 MB por hash; os testes
    passam valores menores para rodar rápido."""

    def __init__(self, **parametros):
        self.ph = PasswordHasher(**parametros)

    def gerar(self, senha: str) -> str:
        return self.ph.hash(senha)

    def conferir(self, hash_: str, senha: str) -> bool:
        try:
            return self.ph.verify(hash_, senha)
        except (VerificationError, InvalidHashError):
            return False

    def precisa_refazer(self, hash_: str) -> bool:
        return self.ph.check_needs_rehash(hash_)


class Cifra:
    """Cifra simétrica para dados pessoais guardados no banco (RNE-005)."""

    def __init__(self, chave: str):
        self.fernet = Fernet(chave)

    @staticmethod
    def nova_chave() -> str:
        return Fernet.generate_key().decode()

    def cifrar(self, texto: str) -> str:
        return self.fernet.encrypt(texto.encode()).decode()

    def decifrar(self, cifrado: str) -> str:
        try:
            return self.fernet.decrypt(cifrado.encode()).decode()
        except InvalidToken as e:
            raise ValueError("dado cifrado com outra chave ou corrompido") from e


def novo_token() -> str:
    """Token aleatório de 256 bits para sessão, desafio de 2FA e recuperação."""
    return secrets.token_urlsafe(32)


def resumo(token: str) -> str:
    """O banco guarda só o SHA-256 do token: um vazamento da tabela não dá acesso."""
    return hashlib.sha256(token.encode()).hexdigest()


def iguais(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode(), b.encode())


# --- TOTP (RFC 6238), compatível com Google Authenticator, Authy e similares ---

EMISSOR = "Nox"


def novo_segredo_totp() -> str:
    return pyotp.random_base32()


def uri_totp(segredo: str, email: str) -> str:
    return pyotp.TOTP(segredo).provisioning_uri(name=email, issuer_name=EMISSOR)


def qr_svg(uri: str) -> str:
    """QR code do endereço otpauth, como imagem SVG em data URI. O SVG usado
    dentro de <img> precisa declarar o xmlns; o svg_inline do segno omite."""
    return segno.make(uri, error="m").svg_data_uri(scale=5, dark="#151a36", light="#eee7d0", border=2)


def passo_valido(segredo: str, codigo: str, agora: float, ultimo_passo: int) -> int | None:
    """Confere o código de 6 dígitos aceitando um passo de 30 s para trás ou
    para frente (relógio do celular adiantado ou atrasado). Devolve o passo
    usado, ou None. Um passo já usado é recusado, para o mesmo código não
    servir duas vezes."""
    if not (codigo.isdigit() and len(codigo) == 6):
        return None
    totp = pyotp.TOTP(segredo)
    atual = int(agora // totp.interval)
    for passo in (atual, atual - 1, atual + 1):
        if passo <= ultimo_passo:
            continue
        if iguais(totp.at(passo * totp.interval), codigo):
            return passo
    return None
