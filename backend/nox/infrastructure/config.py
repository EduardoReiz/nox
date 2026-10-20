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
