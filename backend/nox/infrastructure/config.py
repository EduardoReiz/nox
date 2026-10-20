"""Endereços e credenciais do ambiente local, lidos do .env na raiz do projeto."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[3] / ".env")


def postgres_dsn() -> str:
    senha = os.environ["NOX_PG_SENHA"]
    host = os.environ.get("NOX_PG_HOST", "localhost")
    return f"postgresql://nox:{senha}@{host}:5432/nox"


def influx() -> dict:
    return {
        "url": os.environ.get("NOX_INFLUX_URL", "http://localhost:8086"),
        "token": os.environ["NOX_INFLUX_TOKEN"],
        "org": "nox",
        "bucket": os.environ.get("NOX_INFLUX_BUCKET", "mercado"),
    }


def chave_dados() -> str:
    """Chave da cifra dos dados pessoais (RNE-005). Gerar com
    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"."""
    return os.environ["NOX_CHAVE_DADOS"]


def cookie_seguro() -> bool:
    """Em produção o cookie só trafega por HTTPS (RNF-003). Localhost usa HTTP."""
    return os.environ.get("NOX_COOKIE_SEGURO", "0") == "1"


def vapid() -> dict | None:
    """Chaves das notificações push. Sem elas, o canal push fica desligado."""
    privada, publica = os.environ.get("NOX_VAPID_PRIVADA"), os.environ.get("NOX_VAPID_PUBLICA")
    if not privada or not publica:
        return None
    return {"privada": privada, "publica": publica,
            "contato": os.environ.get("NOX_VAPID_CONTATO", "mailto:contato@nox.invalid")}


def telegram() -> dict | None:
    """Token e nome do bot criado no @BotFather. Sem eles, o Telegram fica desligado."""
    token, bot = os.environ.get("NOX_TELEGRAM_TOKEN"), os.environ.get("NOX_TELEGRAM_BOT")
    if not token or not bot:
        return None
    return {"token": token, "bot": bot.lstrip("@")}
