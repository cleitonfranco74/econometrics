#!/usr/bin/env bash
# 02a - Baixa os arquivos do Cadastro CNPJ (Receita Federal, dados abertos).
#
# Fonte padrão: espelho no GitHub do release 2024.09 (cópia fiel dos arquivos
# publicados pela Receita em set/2024), muito mais rápido que o servidor da
# Receita:  https://github.com/jonathands/dados-abertos-receita-cnpj
#
# Uso (de dentro de codigo/):
#   bash 02a_baixar_cnpj.sh                 # GitHub, release 2024.09
#   bash 02a_baixar_cnpj.sh receita 2026-10 # servidor da Receita (lento)
set -u
FONTE="${1:-github}"
REF="${2:-2024-09}"
DEST="$(cd "$(dirname "$0")/.." && pwd)/dados/brutos/cnpj_$REF"
mkdir -p "$DEST"; cd "$DEST"

if [ "$FONTE" = "github" ]; then
  export URL="https://github.com/jonathands/dados-abertos-receita-cnpj/releases/download/${REF/-/.}"
  export AUTH=""
else
  # pasta pública da Receita: arquivos.receitafederal.gov.br/index.php/s/gn672Ad4CF8N6TK
  export URL="https://arquivos.receitafederal.gov.br/public.php/webdav/Dados/Cadastros/CNPJ/$REF"
  export AUTH="gn672Ad4CF8N6TK:"
fi

ARQS="Simples.zip Municipios.zip Naturezas.zip Cnaes.zip"
for i in 0 1 2 3 4 5 6 7 8 9; do ARQS="$ARQS Estabelecimentos$i.zip Empresas$i.zip"; done

baixa() {  # retoma downloads interrompidos (-C -) e tenta até 5 vezes
  for t in 1 2 3 4 5; do
    if unzip -tq "$1" >/dev/null 2>&1; then echo "ok $1"; return; fi
    if [ -n "$AUTH" ]; then
      curl -sSL -C - --retry 3 -u "$AUTH" -o "$1" "$URL/$1"
    else
      curl -sSL -C - --retry 3 -o "$1" "$URL/$1"
    fi
    sleep 2
  done
  echo "FALHOU $1"
}
export -f baixa
echo $ARQS | tr ' ' '\n' | xargs -P 4 -I{} bash -c 'baixa {}'
echo "FONTE=$FONTE REFERENCIA=$REF" > referencia.txt
echo "FIM"
