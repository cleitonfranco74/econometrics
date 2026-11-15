#!/usr/bin/env bash
# 02a - Baixa os arquivos do Cadastro CNPJ (Receita Federal, dados abertos).
# Pasta pública: https://arquivos.receitafederal.gov.br/index.php/s/gn672Ad4CF8N6TK
# (Dados > Cadastros > CNPJ > AAAA-MM). São ~7 GB compactados.
# Uso (de dentro de codigo/):  bash 02a_baixar_cnpj.sh 2026-10
set -u
REF="${1:-2026-10}"
DEST="$(cd "$(dirname "$0")/.." && pwd)/dados/brutos/cnpj"
mkdir -p "$DEST"; cd "$DEST"
export W="https://arquivos.receitafederal.gov.br/public.php/webdav/Dados/Cadastros/CNPJ/$REF"
ARQS="Simples.zip Municipios.zip Naturezas.zip Cnaes.zip"
for i in 0 1 2 3 4 5 6 7 8 9; do ARQS="$ARQS Estabelecimentos$i.zip Empresas$i.zip"; done

baixa() {  # retoma downloads interrompidos (-C -) e tenta até 5 vezes
  for t in 1 2 3 4 5; do
    if unzip -tq "$1" >/dev/null 2>&1; then echo "ok $1"; return; fi
    curl -sS -C - --retry 3 -u "gn672Ad4CF8N6TK:" -o "$1" "$W/$1"
    echo "tentativa $t de $1 terminou"; sleep 5
  done
  echo "FALHOU $1"
}
export -f baixa
echo $ARQS | tr ' ' '\n' | xargs -P 5 -I{} bash -c 'baixa {}'
echo "REFERENCIA=$REF" > referencia.txt
echo "FIM"
