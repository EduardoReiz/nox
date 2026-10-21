#!/bin/sh
# Gera o .docx e o PDF. Roda duas vezes: a primeira descobre as páginas de
# cada título, a segunda escreve o sumário com elas.
set -e
cd "$(dirname "$0")"
NOME=$(node -e "import('./conteudo.mjs').then(m=>console.log(m.META.arquivo))")
for passo in 1 2; do
  node gerar.mjs
  soffice --headless --convert-to pdf "$NOME.docx" >/dev/null 2>&1
  node paginas.mjs
done
echo "gerado $NOME.pdf"

# Copia para a pasta "Projeto Nox/documentação" do Google Drive, se estiver sincronizada.
DRIVE="$HOME/Google Drive/Meu Drive/Projeto Nox/documentação"
if [ -d "$HOME/Google Drive/Meu Drive/Projeto Nox" ]; then
  mkdir -p "$DRIVE"
  cp "$NOME.docx" "$NOME.pdf" "$DRIVE/"
  echo "copiado para o Google Drive"
fi
