"""API do Nox para o frontend (bloco de Entrega).

O frontend consulta esta API, e nunca a exchange (seção 18.2). Rodar com:

    uvicorn nox.api.app:app --port 8000
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from nox.application.sinais import ServicoSinais

app = FastAPI(title="Nox", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["GET"])
servico = ServicoSinais()


@app.get("/api/sinais")
def listar_sinais() -> list[dict]:
    """Feed: o sinal mais recente de cada ativo acompanhado (RF-008, RF-009)."""
    return servico.sinais()


@app.get("/api/sinais/{ativo}")
def detalhar_sinal(ativo: str) -> dict:
    """Modo Explicativo de um ativo (RF-005)."""
    for s in servico.sinais():
        if s["ativo"] == ativo.upper():
            return s
    raise HTTPException(404, "ativo não acompanhado")


@app.get("/api/ativos/{ativo}/velas")
def velas(ativo: str, quantidade: int = Query(168, ge=10, le=300)) -> list[dict]:
    """Preços de fechamento para o gráfico do dashboard."""
    try:
        return servico.velas(ativo.upper(), quantidade)
    except KeyError:
        raise HTTPException(404, "ativo não acompanhado") from None
