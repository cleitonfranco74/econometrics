"""
01 - Transações Pix por município (Banco Central do Brasil, API Olinda).

Fonte: https://olinda.bcb.gov.br/olinda/servico/Pix_DadosAbertos/versao/v1/odata
Série: TransacoesPixPorMunicipio (mensal, a partir de nov/2020).

Saída: dados/processados/pix_municipio_mes.csv
  - uma linha por município x mês (MT, MS e GO)
  - QT_* = quantidade de transações; VL_* = valor (R$);
    QT_PES_* = quantidade de pessoas/empresas distintas.

Execute de dentro da pasta codigo/:  python 01_pix_bcb.py
"""
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
BRUTOS = RAIZ / "dados" / "brutos"
PROC = RAIZ / "dados" / "processados"
BRUTOS.mkdir(parents=True, exist_ok=True)
PROC.mkdir(parents=True, exist_ok=True)

URL = ("https://olinda.bcb.gov.br/olinda/servico/Pix_DadosAbertos/versao/v1/"
       "odata/TransacoesPixPorMunicipio(DataBase=@DataBase)")
UFS = {50: "MS", 51: "MT", 52: "GO"}


def baixar_uf(cod_uf):
    """Baixa todas as linhas de um estado (cabem numa única consulta)."""
    params = {
        "@DataBase": "'202011'",
        "$filter": f"Estado_Ibge eq {cod_uf}",
        "$format": "json",
        "$top": "200000",
    }
    url = URL + "?" + urllib.parse.urlencode(
        params, safe="@$'", quote_via=urllib.parse.quote)
    for tentativa in range(5):  # o servidor do BCB às vezes falha; tenta de novo
        try:
            with urllib.request.urlopen(url, timeout=600) as r:
                return json.loads(r.read())["value"]
        except Exception as erro:
            print(f"  tentativa {tentativa + 1} falhou ({erro}); aguardando...")
            time.sleep(20)
    raise RuntimeError(f"Não foi possível baixar a UF {cod_uf}")


tudo = []
for cod, sigla in UFS.items():
    lote = baixar_uf(cod)
    print(f"{sigla}: {len(lote)} linhas")
    tudo += lote

(BRUTOS / "pix_municipio.json").write_text(json.dumps(tudo))
pix = pd.DataFrame(tudo)
pix["UF"] = pix["Estado_Ibge"].map(UFS)
pix = pix.rename(columns={"Municipio_Ibge": "cod_ibge", "AnoMes": "anomes"})
pix = pix.drop(columns=["Estado", "Sigla_Regiao", "Regiao"])
pix = pix.sort_values(["cod_ibge", "anomes"]).drop_duplicates(["cod_ibge", "anomes"])

# Transações Pix com ao menos uma PJ (pagadora ou recebedora).
# Atenção: uma transação PJ->PJ entre dois CNPJs do mesmo município aparece
# como pagadora E recebedora; por isso guardamos também os componentes.
pix["qt_pix_pj"] = pix["QT_PagadorPJ"] + pix["QT_RecebedorPJ"]
pix["vl_pix_pj"] = pix["VL_PagadorPJ"] + pix["VL_RecebedorPJ"]
pix["qt_pix_total"] = pix["QT_PagadorPF"] + pix["QT_PagadorPJ"]
pix.to_csv(PROC / "pix_municipio_mes.csv", index=False)
print(pix.shape, pix.anomes.min(), "a", pix.anomes.max(),
      "|", pix.cod_ibge.nunique(), "municípios")
