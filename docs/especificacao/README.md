# Documento de Especificação

`Especificacao_Projeto_Nox_4P_Fase02_REV02.docx` e `.pdf` são gerados a partir de:

- `conteudo.mjs`: o texto do documento, seção por seção. É o arquivo a editar a cada entrega (e o `META.versao`/`META.arquivo` quando mudar a versão);
- `gerar.mjs`: a formatação no modelo da UniEVANGÉLICA (cabeçalho, rodapé, tabelas e quadros de requisitos);
- `diagramas/`: as figuras 1, 4 e 6 em HTML/SVG (`node diagramas/render.mjs` gera os PNG em `figuras/`).

Para gerar o .docx e o PDF (precisa do LibreOffice, `brew install --cask libreoffice`):

```bash
npm install
./exportar_pdf.sh
```

O script gera o PDF duas vezes: a primeira descobre a página de cada título e a segunda escreve o sumário com elas (`paginas.json`).
