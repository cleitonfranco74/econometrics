"""
04 - Covariáveis municipais (IBGE/SIDRA e Ipeadata/Atlas Brasil).

  pop     : população residente estimada (SIDRA 6579, var. 9324) e
            Censo 2022 (SIDRA 4709, var. 93); 2023 interpolado.
  pib     : PIB a preços correntes, R$ mil (SIDRA 5938, var. 37), 2019-2023.
  idhm    : IDHM 2010 (Atlas do Desenvolvimento Humano, série ADH_IDHM
            do Ipeadata).

Saída: dados/processados/covariaveis_municipio_ano.csv
       (uma linha por município x ano, 2019-2024; pib_pc = PIB / pop)

Execute de dentro de codigo/:  python 04_covariaveis_ibge.py
"""
import json
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
BRUTOS = RAIZ / "dados" / "brutos" / "ibge"
PROC = RAIZ / "dados" / "processados"
BRUTOS.mkdir(parents=True, exist_ok=True)

UFS = "50,51,52"  # MS, MT, GO


def sidra(tabela, variavel, periodos, nome):
    url = (f"https://apisidra.ibge.gov.br/values/t/{tabela}/n6/in%20n3%20{UFS}"
           f"/v/{variavel}/p/{periodos}")
    with urllib.request.urlopen(url, timeout=300) as r:
        bruto = r.read()
    (BRUTOS / f"sidra_{tabela}.json").write_bytes(bruto)
    d = pd.DataFrame(json.loads(bruto)[1:])
    d = d.rename(columns={"D1C": "cod_ibge", "D3N": "ano", "V": nome})
    d[nome] = pd.to_numeric(d[nome], errors="coerce")
    d["cod_ibge"] = d["cod_ibge"].astype(int)
    d["ano"] = d["ano"].astype(int)
    return d[["cod_ibge", "ano", nome]]


pop = sidra(6579, 9324, "2019,2020,2021,2024", "pop")
censo = sidra(4709, 93, "2022", "pop")
pop = pd.concat([pop, censo])
pib = sidra(5938, 37, "2019,2020,2021,2022,2023", "pib_mil")

# IDHM 2010 (Ipeadata)
url = "https://www.ipeadata.gov.br/api/odata4/ValoresSerie(SERCODIGO='ADH_IDHM')"
with urllib.request.urlopen(url, timeout=300) as r:
    bruto = r.read()
(BRUTOS / "ipeadata_ADH_IDHM.json").write_bytes(bruto)
idhm = pd.DataFrame(json.loads(bruto)["value"])
idhm = idhm[idhm.VALDATA.str.startswith("2010")
            & idhm.TERCODIGO.str[:2].isin(["50", "51", "52"])]
idhm = idhm.assign(cod_ibge=idhm.TERCODIGO.astype(int),
                   idhm_2010=idhm.VALVALOR)[["cod_ibge", "idhm_2010"]]

# Painel município x ano 2019-2024
muns = sorted(set(pop.cod_ibge))
grade = pd.MultiIndex.from_product([muns, range(2019, 2025)],
                                   names=["cod_ibge", "ano"]).to_frame(index=False)
cov = grade.merge(pop, how="left").merge(pib, how="left")
cov = cov.sort_values(["cod_ibge", "ano"])
cov["pop_imputada"] = cov["pop"].isna().astype(int)        # 2023
cov["pop"] = cov.groupby("cod_ibge")["pop"].transform(
    lambda s: s.interpolate(limit_area="inside"))
cov["pib_imputado"] = cov["pib_mil"].isna().astype(int)    # 2024
cov["pib_mil"] = cov.groupby("cod_ibge")["pib_mil"].ffill()
cov["pib_pc"] = cov["pib_mil"] * 1000 / cov["pop"]
cov = cov.merge(idhm, how="left")
cov["uf"] = (cov.cod_ibge // 100000).map({50: "MS", 51: "MT", 52: "GO"})
cov.to_csv(PROC / "covariaveis_municipio_ano.csv", index=False)
print(cov.shape, "| sem IDHM:", cov.loc[cov.idhm_2010.isna(), "cod_ibge"].nunique(),
      "municípios (criados após 2010)")
print(cov[cov.ano == 2019].describe().T[["mean", "min", "max"]])
