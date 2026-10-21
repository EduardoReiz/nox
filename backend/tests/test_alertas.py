import json
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from pywebpush import WebPushException

from nox.application.alertas import ServicoAlertas
from nox.application.perfil import ServicoPerfil
from nox.domain.alertas import deve_alertar
from nox.domain.contas import Usuario
from nox.infrastructure.contas_repo import ContasMemoria
from nox.infrastructure.notificacoes import CanalPush, ClienteTelegram
from nox.infrastructure.seguranca import Cifra
from nox.infrastructure.sinais_repo import SinaisMemoria

ATIVOS = {"BTCUSDT": "Bitcoin", "ETHUSDT": "Ethereum"}
T0 = datetime(2026, 10, 20, 12, tzinfo=UTC)
INSCRICAO = {"endpoint": "https://push.exemplo/abc", "keys": {"p256dh": "p", "auth": "a"}}


def sinal(ativo, acao, score=70):
    return {"ativo": ativo, "nome": ATIVOS[ativo], "disponivel": True, "acao": acao, "score": score,
            "direcao": "alta", "componentes": [], "divergencia": None, "gerado_em": T0.isoformat(),
            "explicacao": f"Leitura do Nox para {ativo[:3]}: {acao}."}


class Fonte:
    """Simula o cálculo dos sinais: cada chamada devolve a próxima rodada."""

    def __init__(self):
        self.rodadas = []

    def __call__(self):
        return self.rodadas.pop(0) if self.rodadas else []


class PushFalso:
    def __init__(self):
        self.enviados = []
        self.falhar_com = None

    def __call__(self, subscription_info, data, vapid_private_key, vapid_claims, ttl):
        if self.falhar_com:
            raise WebPushException("erro", response=httpx.Response(self.falhar_com))
        self.enviados.append((subscription_info, json.loads(data)))


class TelegramFalso:
    def __init__(self):
        self.enviados = []
        self.updates = []

    def handler(self, req):
        if req.url.path.endswith("sendMessage"):
            corpo = json.loads(req.content)
            self.enviados.append((corpo["chat_id"], corpo["text"]))
            return httpx.Response(200, json={"ok": True, "result": {}})
        oferecidos, self.updates = self.updates, []
        return httpx.Response(200, json={"ok": True, "result": oferecidos})


@pytest.fixture
def ctx():
    contas, sinais = ContasMemoria(), SinaisMemoria()
    perfil = ServicoPerfil(contas, Cifra(Cifra.nova_chave()), ATIVOS)
    fonte, push, tg = Fonte(), PushFalso(), TelegramFalso()
    cliente_tg = ClienteTelegram("token", http=httpx.Client(base_url="https://tg/", transport=httpx.MockTransport(tg.handler)))
    servico = ServicoAlertas(contas, sinais, perfil, fonte, CanalPush("chave", "mailto:x@y.z", enviar=push),
                             cliente_tg, url_app="https://nox.app")
    return servico, contas, sinais, perfil, fonte, push, tg


def usuario(contas, perfil, nome="Ana", frequencia="cada_sinal", lista=("BTCUSDT",), push=True, chat=None):
    u = Usuario(email=f"{nome.lower()}@exemplo.com", nome=nome, senha_hash="x", criado_em=T0,
                frequencia_alerta=frequencia)
    contas.criar_usuario(u)
    perfil.salvar_lista(u, list(lista))
    if push:
        perfil.conectar_push(u, INSCRICAO)
    if chat:
        perfil.vincular_telegram(perfil.iniciar_vinculo_telegram(u), chat)
    return u


@pytest.mark.parametrize("antes,depois,alerta", [
    (None, "manter", False), (None, "comprar", True), ("manter", "manter", False),
    ("manter", "comprar", True), ("comprar", "vender", True), ("comprar", "manter", True),
])
def test_quando_vira_alerta(antes, depois, alerta):
    assert deve_alertar(antes, depois) is alerta


def test_mudanca_gera_alerta_so_para_quem_acompanha(ctx):
    servico, contas, sinais, perfil, fonte, push, tg = ctx
    usuario(contas, perfil, "Ana", lista=["BTCUSDT"], chat="111")
    usuario(contas, perfil, "Bia", lista=["ETHUSDT"])
    fonte.rodadas = [[(sinal("BTCUSDT", "manter", 20), T0)],
                     [(sinal("BTCUSDT", "comprar", 72), T0 + timedelta(hours=1))]]
    assert servico.ciclo() == []  # primeiro sinal, manter: sem alerta
    mudancas = servico.ciclo()
    assert [(m.ativo, m.acao_anterior, m.acao) for m in mudancas] == [("BTCUSDT", "manter", "comprar")]
    assert len(push.enviados) == 1  # só a Ana acompanha o BTC
    _, dados = push.enviados[0]
    assert dados["titulo"] == "Bitcoin: o Nox vê sinal de alta"
    assert dados["url"] == "https://nox.app/sinais/BTCUSDT"
    assert "não é recomendação nem consultoria" in dados["texto"]  # RF-013
    chat, texto = tg.enviados[0]
    assert chat == "111" and "Leitura do Nox para BTC: comprar." in texto and "não é recomendação nem consultoria" in texto


def test_mesma_vela_nao_gera_sinal_nem_alerta_duas_vezes(ctx):
    servico, contas, sinais, perfil, fonte, push, _ = ctx
    usuario(contas, perfil)
    fonte.rodadas = [[(sinal("BTCUSDT", "comprar"), T0)], [(sinal("BTCUSDT", "comprar"), T0)]]
    servico.ciclo()
    servico.ciclo()
    assert len(sinais.sinais) == 1 and len(push.enviados) == 1


def test_sinal_guardado_com_explicacao(ctx):
    servico, _, sinais, _, fonte, _, _ = ctx
    fonte.rodadas = [[(sinal("ETHUSDT", "vender", 66), T0)]]
    servico.ciclo()
    guardado = sinais.ultimo("ETHUSDT")
    assert guardado["score"] == 66 and guardado["explicacao"].startswith("Leitura do Nox para ETH: vender")


def test_resumo_diario_acumula_e_envia_uma_vez(ctx):
    servico, contas, sinais, perfil, fonte, push, _ = ctx
    usuario(contas, perfil, frequencia="resumo_diario", lista=["BTCUSDT", "ETHUSDT"])
    fonte.rodadas = [[(sinal("BTCUSDT", "comprar"), T0), (sinal("ETHUSDT", "vender"), T0)]]
    servico.ciclo()
    assert push.enviados == []  # nada na hora
    assert servico.enviar_resumos() == 1
    titulo = push.enviados[0][1]["titulo"]
    assert titulo == "Nox: 2 mudanças nos seus ativos hoje"
    assert servico.enviar_resumos() == 0


def test_inscricao_cancelada_desconecta_o_push(ctx):
    servico, contas, sinais, perfil, fonte, push, _ = ctx
    u = usuario(contas, perfil)
    push.falhar_com = 410
    fonte.rodadas = [[(sinal("BTCUSDT", "comprar"), T0)]]
    servico.ciclo()
    assert perfil.destino(u.id, "push") is None
    assert sinais.alertas(u.id)[0]["status"] == "falhou"


def test_quem_nao_tem_canal_ligado_nao_recebe(ctx):
    servico, contas, sinais, perfil, fonte, push, _ = ctx
    u = usuario(contas, perfil, push=False)
    fonte.rodadas = [[(sinal("BTCUSDT", "comprar"), T0)]]
    servico.ciclo()
    assert push.enviados == [] and sinais.alertas(u.id) == []


def test_start_no_bot_liga_a_conta_ao_chat(ctx):
    servico, contas, _, perfil, _, _, tg = ctx
    u = usuario(contas, perfil, push=False)
    codigo = perfil.iniciar_vinculo_telegram(u)
    tg.updates = [{"update_id": 5, "message": {"text": f"/start {codigo}", "chat": {"id": 4242}}},
                  {"update_id": 6, "message": {"text": "oi", "chat": {"id": 999}}}]
    assert servico.processar_telegram() == 2
    assert perfil.destino(u.id, "telegram") == "4242"
    assert tg.enviados[0][0] == "4242" and tg.enviados[0][1].startswith("Pronto, Ana!")
    assert "Conectar Telegram" in tg.enviados[1][1]


def test_alerta_de_teste(ctx):
    servico, contas, _, perfil, _, push, tg = ctx
    u = usuario(contas, perfil, chat="777")
    assert servico.testar(u) == {"push": "enviado", "telegram": "enviado"}
    assert push.enviados and tg.enviados


def test_push_vai_cifrado_e_o_navegador_consegue_ler():
    """Prova de ponta a ponta da criptografia do Web Push (RFC 8291): um
    receptor local faz o papel do navegador e decifra a mensagem com as chaves
    dele. Sem essa conferência, um erro de cifra só apareceria no celular."""
    import base64
    import os
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer

    import http_ece
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from py_vapid import Vapid01

    b64 = lambda b: base64.urlsafe_b64encode(b).rstrip(b"=").decode()  # noqa: E731
    navegador = ec.generate_private_key(ec.SECP256R1())
    auth = os.urandom(16)
    recebido = {}

    class Receptor(BaseHTTPRequestHandler):
        def do_POST(self):
            recebido["corpo"] = self.rfile.read(int(self.headers["Content-Length"]))
            recebido["autorizacao"] = self.headers["Authorization"]
            self.send_response(201)
            self.end_headers()

        def log_message(self, *a):
            pass

    servidor = HTTPServer(("127.0.0.1", 0), Receptor)
    threading.Thread(target=servidor.handle_request, daemon=True).start()

    vapid = Vapid01()
    vapid.generate_keys()
    chave_privada = b64(vapid.private_key.private_numbers().private_value.to_bytes(32, "big"))
    inscricao = {
        "endpoint": f"http://127.0.0.1:{servidor.server_port}/push",
        "keys": {"p256dh": b64(navegador.public_key().public_bytes(
                     serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)),
                 "auth": b64(auth)},
    }
    CanalPush(chave_privada, "mailto:teste@nox.invalid").enviar(
        inscricao, "Bitcoin: o Nox vê sinal de alta", "Confiança 72 de 100.", "https://nox.app/sinais/BTCUSDT")
    servidor.server_close()

    assert recebido["autorizacao"].startswith("vapid t=")
    claro = http_ece.decrypt(recebido["corpo"], private_key=navegador, auth_secret=auth, version="aes128gcm")
    assert json.loads(claro) == {"titulo": "Bitcoin: o Nox vê sinal de alta", "texto": "Confiança 72 de 100.",
                                 "url": "https://nox.app/sinais/BTCUSDT"}
