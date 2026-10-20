from datetime import UTC, datetime, timedelta
from urllib.parse import unquote

import pyotp
import pytest

from nox.application.autenticacao import ServicoAutenticacao
from nox.domain.contas import ErroDeConta, validar_senha
from nox.infrastructure.contas_repo import ContasMemoria
from nox.infrastructure.email import EmailMemoria
from nox.infrastructure.seguranca import Cifra, Senhas

SENHA = "lua-cheia-sobre-o-mar"
SENHA_NOVA = "estrela-do-sul-2027"
SENHA_OUTRA = "outra-senha-boa-2028"
ERRADA = "senha-errada-123"


class Relogio:
    def __init__(self):
        self.t = datetime(2026, 10, 20, 12, 0, tzinfo=UTC)

    def __call__(self):
        return self.t

    def andar(self, **kw):
        self.t += timedelta(**kw)


@pytest.fixture
def ctx():
    relogio = Relogio()
    repo, email = ContasMemoria(), EmailMemoria()
    # Parâmetros leves do Argon2 só para os testes rodarem rápido.
    s = ServicoAutenticacao(repo, Cifra(Cifra.nova_chave()), email,
                            senhas=Senhas(time_cost=1, memory_cost=1024, parallelism=1), agora=relogio)
    return s, repo, email, relogio


def com_2fa(s, relogio):
    s.cadastrar("Ana", "ana@exemplo.com", SENHA)
    u = s.repo.usuario_por_email("ana@exemplo.com")
    segredo = s.iniciar_2fa(u)["segredo"]
    s.ativar_2fa(s.repo.usuario_por_id(u.id), pyotp.TOTP(segredo).at(relogio()))
    return segredo


# --- regras de senha e cadastro ---------------------------------------------


@pytest.mark.parametrize("senha", ["curta", "1234567890", "aaaaaaaaaaaa", "ana.silva-2026!"])
def test_senhas_recusadas(senha):
    with pytest.raises(ErroDeConta):
        validar_senha(senha, "ana.silva@exemplo.com")


def test_cadastro_guarda_so_o_hash_e_normaliza_o_email(ctx):
    s, repo, _, _ = ctx
    token = s.cadastrar("  Ana   Souza ", "  Ana@Exemplo.COM ", SENHA)
    u = repo.usuario_por_email("ana@exemplo.com")
    assert u.nome == "Ana Souza"
    assert u.senha_hash.startswith("$argon2id$") and SENHA not in u.senha_hash
    assert s.usuario_da_sessao(token).id == u.id
    # O banco guarda só o resumo do token da sessão.
    assert token not in repo.sessoes


def test_email_repetido(ctx):
    s, *_ = ctx
    s.cadastrar("Ana", "ana@exemplo.com", SENHA)
    with pytest.raises(ErroDeConta, match="Já existe"):
        s.cadastrar("Outra", "ANA@exemplo.com", SENHA)


# --- login --------------------------------------------------------------------


def test_login_sem_2fa_abre_sessao(ctx):
    s, *_ = ctx
    s.cadastrar("Ana", "ana@exemplo.com", SENHA)
    r = s.entrar("ana@exemplo.com", SENHA)
    assert r.sessao and r.desafio_2fa is None


def test_mesma_mensagem_para_email_inexistente_e_senha_errada(ctx):
    s, *_ = ctx
    s.cadastrar("Ana", "ana@exemplo.com", SENHA)
    with pytest.raises(ErroDeConta) as a:
        s.entrar("ana@exemplo.com", ERRADA)
    with pytest.raises(ErroDeConta) as b:
        s.entrar("ninguem@exemplo.com", SENHA)
    assert str(a.value) == str(b.value) == "E-mail ou senha incorretos."


def test_bloqueio_depois_de_5_erros_e_libera_depois_de_15_minutos(ctx):
    s, _, _, relogio = ctx
    s.cadastrar("Ana", "ana@exemplo.com", SENHA)
    for _ in range(5):
        with pytest.raises(ErroDeConta):
            s.entrar("ana@exemplo.com", ERRADA)
    with pytest.raises(ErroDeConta, match="Muitas tentativas"):
        s.entrar("ana@exemplo.com", SENHA)  # nem a senha certa entra
    relogio.andar(minutes=16)
    assert s.entrar("ana@exemplo.com", SENHA).sessao


def test_sessao_expira_e_sair_encerra(ctx):
    s, _, _, relogio = ctx
    token = s.cadastrar("Ana", "ana@exemplo.com", SENHA)
    outra = s.entrar("ana@exemplo.com", SENHA).sessao
    s.sair(outra)
    assert s.usuario_da_sessao(outra) is None
    relogio.andar(days=8)
    assert s.usuario_da_sessao(token) is None


# --- verificação em duas etapas -------------------------------------------------


def test_segredo_do_2fa_fica_cifrado(ctx):
    s, repo, _, relogio = ctx
    segredo = com_2fa(s, relogio)
    u = repo.usuario_por_email("ana@exemplo.com")
    assert u.totp_ativo and segredo not in u.totp_cifrado


def test_login_com_2fa_exige_senha_e_depois_codigo(ctx):
    s, _, _, relogio = ctx
    segredo = com_2fa(s, relogio)
    relogio.andar(seconds=60)
    r = s.entrar("ana@exemplo.com", SENHA)
    assert r.sessao is None and r.desafio_2fa
    token = s.confirmar_codigo(r.desafio_2fa, pyotp.TOTP(segredo).at(relogio()))
    assert s.usuario_da_sessao(token).email == "ana@exemplo.com"


def test_codigo_sem_ter_passado_pela_senha_nao_entra(ctx):
    # A falha do protótipo antigo: e-mail e código bastavam para entrar.
    s, _, _, relogio = ctx
    segredo = com_2fa(s, relogio)
    with pytest.raises(ErroDeConta):
        s.confirmar_codigo("ana@exemplo.com", pyotp.TOTP(segredo).at(relogio()))


def test_mesmo_codigo_nao_serve_duas_vezes(ctx):
    s, _, _, relogio = ctx
    segredo = com_2fa(s, relogio)
    relogio.andar(seconds=60)
    codigo = pyotp.TOTP(segredo).at(relogio())
    s.confirmar_codigo(s.entrar("ana@exemplo.com", SENHA).desafio_2fa, codigo)
    with pytest.raises(ErroDeConta):
        s.confirmar_codigo(s.entrar("ana@exemplo.com", SENHA).desafio_2fa, codigo)


def test_desafio_expira_em_5_minutos(ctx):
    s, _, _, relogio = ctx
    segredo = com_2fa(s, relogio)
    relogio.andar(seconds=60)
    desafio = s.entrar("ana@exemplo.com", SENHA).desafio_2fa
    relogio.andar(minutes=6)
    with pytest.raises(ErroDeConta):
        s.confirmar_codigo(desafio, pyotp.TOTP(segredo).at(relogio()))


def test_cinco_codigos_errados_invalidam_o_desafio(ctx):
    s, _, _, relogio = ctx
    segredo = com_2fa(s, relogio)
    relogio.andar(seconds=60)
    desafio = s.entrar("ana@exemplo.com", SENHA).desafio_2fa
    for _ in range(4):
        with pytest.raises(ErroDeConta, match="Código incorreto"):
            s.confirmar_codigo(desafio, "000000")
    with pytest.raises(ErroDeConta, match="Muitos códigos"):
        s.confirmar_codigo(desafio, "000000")
    with pytest.raises(ErroDeConta):
        s.confirmar_codigo(desafio, pyotp.TOTP(segredo).at(relogio()))


def test_codigo_aceita_relogio_do_celular_30_segundos_atrasado(ctx):
    s, _, _, relogio = ctx
    segredo = com_2fa(s, relogio)
    relogio.andar(seconds=90)
    desafio = s.entrar("ana@exemplo.com", SENHA).desafio_2fa
    atrasado = pyotp.TOTP(segredo).at(relogio() - timedelta(seconds=30))
    assert s.confirmar_codigo(desafio, atrasado)


def test_2fa_so_ativa_com_codigo_certo(ctx):
    s, repo, _, _ = ctx
    s.cadastrar("Ana", "ana@exemplo.com", SENHA)
    u = repo.usuario_por_email("ana@exemplo.com")
    dados = s.iniciar_2fa(u)
    # Imagem SVG válida para <img>: precisa declarar o namespace do SVG.
    assert dados["qr"].startswith("data:image/svg+xml")
    assert "xmlns" in unquote(dados["qr"])
    with pytest.raises(ErroDeConta):
        s.ativar_2fa(repo.usuario_por_id(u.id), "123456")
    assert not repo.usuario_por_id(u.id).totp_ativo


def test_desativar_2fa_pede_a_senha(ctx):
    s, repo, _, relogio = ctx
    com_2fa(s, relogio)
    u = repo.usuario_por_email("ana@exemplo.com")
    with pytest.raises(ErroDeConta):
        s.desativar_2fa(u, ERRADA)
    s.desativar_2fa(u, SENHA)
    assert s.entrar("ana@exemplo.com", SENHA).sessao


# --- recuperação de senha --------------------------------------------------------


def token_do_email(email: EmailMemoria) -> str:
    texto = email.enviados[-1][2]
    return texto.split("token=")[1].split()[0]


def test_recuperacao_completa_derruba_sessoes_antigas(ctx):
    s, _, email, _ = ctx
    antiga = s.cadastrar("Ana", "ana@exemplo.com", SENHA)
    s.pedir_recuperacao("ana@exemplo.com")
    s.redefinir_senha(token_do_email(email), SENHA_NOVA)
    assert s.usuario_da_sessao(antiga) is None
    with pytest.raises(ErroDeConta):
        s.entrar("ana@exemplo.com", SENHA)
    assert s.entrar("ana@exemplo.com", SENHA_NOVA).sessao


def test_link_de_recuperacao_vale_uma_vez_e_expira(ctx):
    s, _, email, relogio = ctx
    s.cadastrar("Ana", "ana@exemplo.com", SENHA)
    s.pedir_recuperacao("ana@exemplo.com")
    token = token_do_email(email)
    s.redefinir_senha(token, SENHA_NOVA)
    with pytest.raises(ErroDeConta, match="expirou ou já foi usado"):
        s.redefinir_senha(token, SENHA_OUTRA)
    s.pedir_recuperacao("ana@exemplo.com")
    relogio.andar(minutes=31)
    with pytest.raises(ErroDeConta, match="expirou"):
        s.redefinir_senha(token_do_email(email), SENHA_OUTRA)


def test_pedir_recuperacao_de_email_inexistente_nao_envia_nem_avisa(ctx):
    s, _, email, _ = ctx
    s.pedir_recuperacao("ninguem@exemplo.com")
    s.pedir_recuperacao("isto nem é e-mail")
    assert email.enviados == []


# --- LGPD -------------------------------------------------------------------------


def test_excluir_conta_apaga_dados_e_deixa_auditoria_anonima(ctx):
    s, repo, _, _ = ctx
    token = s.cadastrar("Ana", "ana@exemplo.com", SENHA)
    u = s.usuario_da_sessao(token)
    with pytest.raises(ErroDeConta):
        s.excluir_conta(u, ERRADA)
    s.excluir_conta(u, SENHA)
    assert repo.usuario_por_email("ana@exemplo.com") is None
    assert s.usuario_da_sessao(token) is None
    assert all(uid is None for _, uid, _ in repo.auditoria)
