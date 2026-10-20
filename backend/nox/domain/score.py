"""Score de confiança, divergência e geração do Sinal de Recomendação.

Regras atendidas: RNE-001 (média ponderada dos componentes), RNE-002 e
RNF-005 (explicação guardada no próprio sinal), RNE-003 (redução por
divergência crítica), RNE-004 (sem dados suficientes e atuais, sem sinal),
RNE-006 (sentimento expirado não entra), RNE-007 (aviso de risco) e RNE-008
(abaixo do limiar, a ação é manter).

Como o score é calculado:
  1. Cada componente vira uma força de -1 (aponta queda) a +1 (aponta alta).
  2. A direção do sinal é o sinal da média ponderada das forças.
  3. S de cada componente = quanto ele apoia essa direção, de 0 a 100. Um
     componente neutro ou contrário vale 0.
  4. Score = soma de w·S, e Score final = Score·(1 − r) se houver divergência.

Todos os números marcados como PROVISÓRIO serão calibrados com backtesting.
"""

import math
import statistics
from dataclasses import dataclass, field
from datetime import datetime

from nox.domain.indicadores import macd, rsi
from nox.domain.mercado import INTERVALOS, Vela

PESOS = {"tecnico": 0.5, "sentimento": 0.3, "ml": 0.2}  # PROVISÓRIO
PESO_RSI, PESO_MACD = 0.5, 0.5  # PROVISÓRIO: dentro do componente técnico
LIMIAR_ACAO = 60  # RNE-008, valor inicial proposto no documento
FORCA_DIVERGENCIA = 0.3  # PROVISÓRIO: técnico e sentimento opostos, os dois com pelo menos essa força
REDUCAO_DIVERGENCIA = 0.3  # PROVISÓRIO: fator r
MINIMO_VELAS = 200  # Experimentação 4: antes disso o RSI ainda não estabilizou
JANELA_MACD = 100  # velas usadas para medir a escala típica do histograma

AVISO_RISCO = (
    "Esta recomendação é apenas informativa e não constitui consultoria de investimentos. "
    "O Nox não opera em seu nome. Criptoativos são muito voláteis: decida com cuidado "
    "e invista só o que pode perder."
)


@dataclass(frozen=True)
class MedicaoSentimento:
    ativo: str
    fonte: str
    intensidade: float  # -1 muito negativo, +1 muito positivo
    medido_em: datetime
    expira_em: datetime


@dataclass
class Componente:
    nome: str
    forca: float  # -1 a +1
    peso: float  # já redistribuído entre os componentes presentes
    pontuacao: float = 0.0  # S, de 0 a 100, preenchido depois da direção
    detalhes: dict = field(default_factory=dict)


@dataclass
class Sinal:
    ativo: str
    gerado_em: datetime
    acao: str  # "comprar", "vender" ou "manter"
    score: int
    direcao: str  # "alta", "baixa" ou "neutra"
    componentes: list[Componente]
    ausentes: list[str]
    divergencia: dict | None
    explicacao: str
    aviso_risco: str = AVISO_RISCO


@dataclass
class SemSinal:
    """RNE-004: não há sinal novo, e o motivo é mostrado no lugar."""

    ativo: str
    motivo: str


def _limitar(x: float) -> float:
    return max(-1.0, min(1.0, x))


def forca_rsi(valor: float) -> float:
    """Leitura clássica: abaixo de 30 o ativo está "barato demais" e tende a
    subir (+1); acima de 70, "caro demais" e tende a cair (-1). Entre 40 e 60
    o RSI não diz nada (0), e de 30 a 40 e de 60 a 70 a força cresce aos poucos.
    Sem essa faixa neutra, um RSI de 57 já empurrava o sinal para baixo,
    enquanto a explicação dizia que ele estava neutro."""
    distancia = abs(50 - valor) - 10
    if distancia <= 0:
        return 0.0
    return math.copysign(min(distancia / 10, 1.0), 50 - valor)


def forca_macd(histograma: list[float | None]) -> tuple[float, float]:
    """O MACD está na unidade do preço (centenas no BTC, centésimos no SOL).
    Para virar força, o histograma atual é dividido pela sua variação típica
    recente e passa por tanh, que mantém o resultado entre -1 e +1."""
    valores = [h for h in histograma if h is not None][-JANELA_MACD:]
    escala = statistics.pstdev(valores) if len(valores) > 1 else 0.0
    if escala == 0:
        return 0.0, 0.0
    return math.tanh(valores[-1] / escala), escala


def componente_tecnico(fechamentos: list[float]) -> Componente:
    valor_rsi = rsi(fechamentos)[-1]
    m = macd(fechamentos)
    f_macd, escala = forca_macd(m.histograma)
    f_rsi = forca_rsi(valor_rsi)
    return Componente(
        nome="tecnico",
        forca=PESO_RSI * f_rsi + PESO_MACD * f_macd,
        peso=PESOS["tecnico"],
        detalhes={
            "rsi": round(valor_rsi, 2),
            "forca_rsi": round(f_rsi, 3),
            "macd": round(m.macd[-1], 6),
            "linha_sinal": round(m.sinal[-1], 6),
            "histograma": round(m.histograma[-1], 6),
            "escala_histograma": round(escala, 6),
            "forca_macd": round(f_macd, 3),
            "cruzamento": m.cruzamento,
        },
    )


def componente_sentimento(medicoes: list[MedicaoSentimento], agora: datetime) -> Componente | None:
    validas = [m for m in medicoes if m.medido_em <= agora < m.expira_em]
    if not validas:
        return None
    return Componente(
        nome="sentimento",
        forca=_limitar(statistics.fmean(m.intensidade for m in validas)),
        peso=PESOS["sentimento"],
        detalhes={
            "medicoes_validas": len(validas),
            "medicoes_expiradas": len(medicoes) - len(validas),
            "fontes": sorted({m.fonte for m in validas}),
        },
    )


def verificar_dados(ativo: str, velas: list[Vela], agora: datetime) -> SemSinal | None:
    if len(velas) < MINIMO_VELAS:
        return SemSinal(ativo, f"histórico insuficiente: {len(velas)} velas, o mínimo é {MINIMO_VELAS}")
    ultima = velas[-1]
    passo = INTERVALOS[ultima.intervalo]
    # A última vela fechada termina em instante + passo; mais um intervalo de folga.
    if agora - (ultima.instante + passo) > passo:
        return SemSinal(ativo, f"dados desatualizados: a última vela é de {ultima.instante.isoformat()}")
    return None


@dataclass
class Resultado:
    score: int
    direcao: str
    acao: str
    divergencia: dict | None


def combinar(componentes: list[Componente]) -> Resultado:
    """O núcleo da RNE-001, RNE-003 e RNE-008, só com as forças já calculadas.

    Ajusta os pesos e as pontuações dos componentes recebidos. O componente
    técnico, quando presente, deve se chamar "tecnico" e o de sentimento,
    "sentimento".
    """
    # Os pesos de quem faltou são redistribuídos entre os presentes.
    total = sum(c.peso for c in componentes)
    for c in componentes:
        c.peso = c.peso / total

    media = sum(c.peso * c.forca for c in componentes)
    sentido = 1 if media > 0 else -1 if media < 0 else 0
    for c in componentes:
        c.pontuacao = 100 * max(0.0, c.forca * sentido)
    score = sum(c.peso * c.pontuacao for c in componentes)

    divergencia = None
    tec = next((c for c in componentes if c.nome == "tecnico"), None)
    sent = next((c for c in componentes if c.nome == "sentimento"), None)
    if (tec and sent and tec.forca * sent.forca < 0
            and min(abs(tec.forca), abs(sent.forca)) >= FORCA_DIVERGENCIA):
        divergencia = {
            "tecnico": "alta" if tec.forca > 0 else "baixa",
            "sentimento": "positivo" if sent.forca > 0 else "negativo",
            "score_antes": round(score),
            "reducao": REDUCAO_DIVERGENCIA,
        }
        score *= 1 - REDUCAO_DIVERGENCIA

    score_final = round(score)
    direcao = {1: "alta", -1: "baixa", 0: "neutra"}[sentido]
    if score_final < LIMIAR_ACAO or sentido == 0:
        acao = "manter"
    else:
        acao = "comprar" if sentido > 0 else "vender"
    return Resultado(score_final, direcao, acao, divergencia)


def gerar_sinal(
    ativo: str,
    velas: list[Vela],
    agora: datetime,
    sentimentos: list[MedicaoSentimento] = (),
    forca_ml: float | None = None,
) -> Sinal | SemSinal:
    problema = verificar_dados(ativo, velas, agora)
    if problema:
        return problema

    componentes = [componente_tecnico([v.fechamento for v in velas])]
    ausentes = []
    sent = componente_sentimento(list(sentimentos), agora)
    if sent:
        componentes.append(sent)
    else:
        ausentes.append("sentimento")
    if forca_ml is not None:
        componentes.append(Componente("ml", _limitar(forca_ml), PESOS["ml"]))
    else:
        ausentes.append("ml")

    r = combinar(componentes)
    sinal = Sinal(ativo, agora, r.acao, r.score, r.direcao, componentes, ausentes,
                  r.divergencia, "")
    sinal.explicacao = explicar(sinal)
    return sinal


# ---------------------------------------------------------------------------
# Modo Explicativo (RF-005). Por enquanto o texto sai de modelos fixos; a forma
# definitiva de gerar a explicação ainda será decidida.


def _frase_rsi(valor: float) -> str:
    if valor < 30:
        return (f"o RSI está em {valor:.0f}, abaixo de 30: o preço caiu rápido e muitas vezes "
                "volta a subir depois disso")
    if valor > 70:
        return (f"o RSI está em {valor:.0f}, acima de 70: o preço subiu rápido e muitas vezes "
                "corrige para baixo depois disso")
    if valor < 40:
        return f"o RSI está em {valor:.0f}, chegando perto de 30, a zona em que o preço costuma voltar a subir"
    if valor > 60:
        return f"o RSI está em {valor:.0f}, chegando perto de 70, a zona em que o preço costuma corrigir"
    return f"o RSI está em {valor:.0f}, numa faixa neutra (entre 40 e 60)"


def _frase_macd(d: dict) -> str:
    if d["cruzamento"] == "alta":
        return "o MACD acabou de cruzar para cima, um sinal de que a alta está ganhando força"
    if d["cruzamento"] == "baixa":
        return "o MACD acabou de cruzar para baixo, um sinal de que a queda está ganhando força"
    if d["forca_macd"] > 0.3:
        return "o MACD mostra impulso de alta"
    if d["forca_macd"] < -0.3:
        return "o MACD mostra impulso de queda"
    return "o MACD não mostra impulso claro"


def explicar(s: Sinal) -> str:
    # "BTCUSDT" é o par na exchange; para o usuário basta "BTC".
    moeda = s.ativo.removesuffix("USDT")
    partes = [f"O Nox sugere {s.acao} {moeda}, com confiança {s.score} de 100."]

    tec = next(c for c in s.componentes if c.nome == "tecnico")
    partes.append(f"No gráfico, {_frase_rsi(tec.detalhes['rsi'])}, e {_frase_macd(tec.detalhes)}.")

    sent = next((c for c in s.componentes if c.nome == "sentimento"), None)
    if sent:
        tom = ("positivo" if sent.forca > 0.15 else "negativo" if sent.forca < -0.15 else "neutro")
        partes.append(f"O sentimento das notícias e redes está {tom}.")

    if s.divergencia:
        partes.append(
            f"Atenção: o gráfico aponta {s.divergencia['tecnico']}, mas o sentimento está "
            f"{s.divergencia['sentimento']}. Por essa divergência, a confiança caiu de "
            f"{s.divergencia['score_antes']} para {s.score}.")

    if s.acao == "manter":
        if s.direcao == "neutra":
            partes.append("Os sinais se anulam, então não há motivo para agir agora.")
        else:
            partes.append(
                f"Os sinais apontam levemente para {s.direcao}, mas a confiança está abaixo "
                f"de {LIMIAR_ACAO}, o mínimo para o Nox sugerir comprar ou vender.")

    faltam = {"sentimento": "o sentimento de mercado", "ml": "a previsão de Machine Learning"}
    if s.ausentes:
        partes.append("Este cálculo não usou " + " nem ".join(faltam[a] for a in s.ausentes) + ".")

    return " ".join(partes)
