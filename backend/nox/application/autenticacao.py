"""Cadastro, login, verificação em duas etapas e recuperação de senha (RF-010).

Corrige as falhas registradas na revisão do protótipo de referência
(Experimentação 5): o segundo passo do login exige ter passado pela senha
antes, e o código segue o padrão TOTP dos aplicativos autenticadores.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from nox.domain.contas import (
    ErroDeConta,
    Usuario,
    normalizar_email,
    validar_nome,
    validar_senha,
)
from nox.infrastructure import seguranca
from nox.infrastructure.contas_repo import RepositorioContas
from nox.infrastructure.email import CaixaDeSaida

DURACAO_SESSAO = timedelta(days=7)
DURACAO_DESAFIO_2FA = timedelta(minutes=5)
DURACAO_RECUPERACAO = timedelta(minutes=30)
MAX_FALHAS_LOGIN = 5
JANELA_FALHAS = timedelta(minutes=15)
MAX_FALHAS_CODIGO = 5

CREDENCIAIS_INVALIDAS = "E-mail ou senha incorretos."
CODIGO_INVALIDO = "Código incorreto ou expirado."


@dataclass
class Entrada:
    """Resultado do primeiro passo do login: ou a sessão já está aberta, ou
    falta o código do aplicativo autenticador."""

    sessao: str | None = None
    desafio_2fa: str | None = None


class ServicoAutenticacao:
    def __init__(self, repo: RepositorioContas, cifra: seguranca.Cifra, email: CaixaDeSaida,
                 senhas: seguranca.Senhas | None = None, url_app: str = "http://localhost:5173",
                 agora=lambda: datetime.now(UTC)):
        self.repo = repo
        self.cifra = cifra
        self.email = email
        self.senhas = senhas or seguranca.Senhas()
        self.url_app = url_app
        self.agora = agora
        # Hash de uma senha qualquer, conferido quando o e-mail não existe, para
        # o tempo de resposta não revelar quais e-mails têm conta.
        self._hash_falso = self.senhas.gerar("senha-que-nao-existe")

    # --- cadastro e sessão ---------------------------------------------------

    def cadastrar(self, nome: str, email: str, senha: str) -> str:
        email = normalizar_email(email)
        nome = validar_nome(nome)
        validar_senha(senha, email)
        u = Usuario(email=email, nome=nome, senha_hash=self.senhas.gerar(senha), criado_em=self.agora())
        self.repo.criar_usuario(u)
        self.repo.registrar("conta_criada", u.id, self.agora())
        return self._abrir_sessao(u.id)

    def _abrir_sessao(self, usuario_id: str) -> str:
        token = seguranca.novo_token()
        self.repo.criar_sessao(seguranca.resumo(token), usuario_id, self.agora() + DURACAO_SESSAO)
        self.repo.registrar("sessao_aberta", usuario_id, self.agora())
        return token

    def usuario_da_sessao(self, token: str | None) -> Usuario | None:
        if not token:
            return None
        uid = self.repo.usuario_da_sessao(seguranca.resumo(token), self.agora())
        return self.repo.usuario_por_id(uid) if uid else None

    def sair(self, token: str) -> None:
        self.repo.apagar_sessao(seguranca.resumo(token))

    # --- login em dois passos ------------------------------------------------

    def entrar(self, email: str, senha: str) -> Entrada:
        try:
            email = normalizar_email(email)
        except ErroDeConta:
            raise ErroDeConta(CREDENCIAIS_INVALIDAS) from None
        u = self.repo.usuario_por_email(email)
        if u is None:
            self.senhas.conferir(self._hash_falso, senha)
            raise ErroDeConta(CREDENCIAIS_INVALIDAS)

        agora = self.agora()
        if self.repo.contar_eventos(u.id, "login_falhou", agora - JANELA_FALHAS) >= MAX_FALHAS_LOGIN:
            raise ErroDeConta("Muitas tentativas erradas. Espere 15 minutos e tente de novo.")
        if not self.senhas.conferir(u.senha_hash, senha):
            self.repo.registrar("login_falhou", u.id, agora)
            raise ErroDeConta(CREDENCIAIS_INVALIDAS)

        if self.senhas.precisa_refazer(u.senha_hash):
            u.senha_hash = self.senhas.gerar(senha)
            self.repo.atualizar_usuario(u)

        if u.totp_ativo:
            token = seguranca.novo_token()
            self.repo.apagar_desafios(u.id, "2fa")
            self.repo.criar_desafio("2fa", seguranca.resumo(token), u.id, agora + DURACAO_DESAFIO_2FA)
            return Entrada(desafio_2fa=token)
        return Entrada(sessao=self._abrir_sessao(u.id))

    def confirmar_codigo(self, desafio: str, codigo: str) -> str:
        """Segundo passo: só vale com o desafio criado depois da senha certa."""
        h = seguranca.resumo(desafio)
        uid = self.repo.usuario_do_desafio("2fa", h, self.agora())
        u = self.repo.usuario_por_id(uid) if uid else None
        if u is None or not u.totp_ativo:
            raise ErroDeConta(CODIGO_INVALIDO)
        passo = seguranca.passo_valido(self.cifra.decifrar(u.totp_cifrado), codigo.strip(),
                                       self.agora().timestamp(), u.totp_ultimo_passo)
        if passo is None:
            self.repo.registrar("codigo_2fa_falhou", u.id, self.agora())
            if self.repo.falhar_desafio(h) >= MAX_FALHAS_CODIGO:
                self.repo.apagar_desafios(u.id, "2fa")
                raise ErroDeConta("Muitos códigos errados. Entre com a senha de novo.")
            raise ErroDeConta(CODIGO_INVALIDO)
        u.totp_ultimo_passo = passo
        self.repo.atualizar_usuario(u)
        self.repo.apagar_desafios(u.id, "2fa")
        return self._abrir_sessao(u.id)

    # --- ativar a verificação em duas etapas ---------------------------------

    def iniciar_2fa(self, u: Usuario) -> dict:
        """Gera um segredo novo, ainda inativo, e devolve o QR code para o aplicativo."""
        if u.totp_ativo:
            raise ErroDeConta("A verificação em duas etapas já está ativa.")
        segredo = seguranca.novo_segredo_totp()
        u.totp_cifrado = self.cifra.cifrar(segredo)
        u.totp_ultimo_passo = 0
        self.repo.atualizar_usuario(u)
        uri = seguranca.uri_totp(segredo, u.email)
        return {"qr": seguranca.qr_svg(uri), "segredo": segredo}

    def ativar_2fa(self, u: Usuario, codigo: str) -> None:
        """Só ativa depois que a pessoa prova que o aplicativo gera o código certo."""
        if u.totp_ativo or not u.totp_cifrado:
            raise ErroDeConta("Comece a configuração da verificação em duas etapas de novo.")
        passo = seguranca.passo_valido(self.cifra.decifrar(u.totp_cifrado), codigo.strip(),
                                       self.agora().timestamp(), u.totp_ultimo_passo)
        if passo is None:
            raise ErroDeConta(CODIGO_INVALIDO)
        u.totp_ativo = True
        u.totp_ultimo_passo = passo
        self.repo.atualizar_usuario(u)
        self.repo.registrar("2fa_ativado", u.id, self.agora())

    def desativar_2fa(self, u: Usuario, senha: str) -> None:
        if not self.senhas.conferir(u.senha_hash, senha):
            raise ErroDeConta("Senha incorreta.")
        u.totp_ativo = False
        u.totp_cifrado = None
        self.repo.atualizar_usuario(u)
        self.repo.registrar("2fa_desativado", u.id, self.agora())

    # --- recuperação de senha ------------------------------------------------

    def pedir_recuperacao(self, email: str) -> None:
        """A resposta para quem chama é sempre a mesma, exista a conta ou não."""
        try:
            u = self.repo.usuario_por_email(normalizar_email(email))
        except ErroDeConta:
            return
        if u is None:
            return
        token = seguranca.novo_token()
        self.repo.apagar_desafios(u.id, "recuperacao")
        self.repo.criar_desafio("recuperacao", seguranca.resumo(token), u.id,
                                self.agora() + DURACAO_RECUPERACAO)
        self.repo.registrar("recuperacao_pedida", u.id, self.agora())
        self.email.enviar(
            u.email, "Redefinir sua senha do Nox",
            f"Olá, {u.nome}.\n\nPara criar uma senha nova, abra o link abaixo. Ele vale por 30 minutos "
            f"e funciona uma vez só.\n\n{self.url_app}/redefinir-senha?token={token}\n\n"
            "Se você não pediu isso, ignore este e-mail. Sua senha continua a mesma.")

    def redefinir_senha(self, token: str, nova_senha: str) -> None:
        uid = self.repo.usuario_do_desafio("recuperacao", seguranca.resumo(token), self.agora())
        u = self.repo.usuario_por_id(uid) if uid else None
        if u is None:
            raise ErroDeConta("Este link expirou ou já foi usado. Peça um novo.")
        validar_senha(nova_senha, u.email)
        u.senha_hash = self.senhas.gerar(nova_senha)
        self.repo.atualizar_usuario(u)
        self.repo.apagar_desafios(u.id, "recuperacao")
        # Quem estava conectado com a senha antiga perde o acesso.
        self.repo.apagar_sessoes(u.id)
        self.repo.registrar("senha_redefinida", u.id, self.agora())

    # --- direitos do titular (LGPD) ------------------------------------------

    def excluir_conta(self, u: Usuario, senha: str) -> None:
        if not self.senhas.conferir(u.senha_hash, senha):
            raise ErroDeConta("Senha incorreta.")
        self.repo.registrar("conta_excluida", u.id, self.agora())
        self.repo.apagar_usuario(u.id)
