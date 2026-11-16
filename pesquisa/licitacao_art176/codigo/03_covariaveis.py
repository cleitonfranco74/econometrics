"""
03 - Covariáveis municipais do Paraná.

  População : IBGE/SIDRA 6579 (estimativas 2018-2021, 2024-2025) e
              SIDRA 4709 (Censo 2022). 2023 = interpolação.
  PIB       : IBGE/SIDRA 5938 (PIB a preços correntes), 2019.
  Fiscais 2019 (SICONFI/Tesouro, API apidatalake):
     DCA Anexo I-C: receitas correntes, impostos/taxas (1.1), patrimonial
                    (1.3), cota-parte do FPM (1.7.1.8.01.2.0)
     DCA Anexo I-D: despesa liquidada com Pessoal e Encargos (3.1), usada
                    como pessoal / receita corrente (todos os municípios)
     RGF Anexo 1: % pessoal / RCL (só ~1/3 dos municípios na API em 2019)
  Distância a Curitiba: distância em linha reta (km) entre as sedes
     (coordenadas: github.com/kelvins/municipios-brasileiros). O projeto
     prevê distância rodoviária; a linear é uma aproximação.

Saída: dados/processados/covariaveis_pr.csv (uma linha por município)
       dados/processados/populacao_pr_ano.csv (município x ano)
"""
import json
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
BRUTOS = RAIZ / "dados" / "brutos" / "covariaveis"
PROC = RAIZ / "dados" / "processados"
BRUTOS.mkdir(parents=True, exist_ok=True)


def get_json(url, tent=5):
    for t in range(tent):
        try:
            with urllib.request.urlopen(url, timeout=180) as r:
                return json.loads(r.read())
        except Exception:
            time.sleep(4 * (t + 1))
    raise RuntimeError(url)


def sidra(tab, var, per, nome):
    url = f"https://apisidra.ibge.gov.br/values/t/{tab}/n6/in%20n3%2041/v/{var}/p/{per}"
    d = pd.DataFrame(get_json(url)[1:])
    d = d.rename(columns={"D1C": "cod_ibge", "D1N": "nome", "D3N": "ano", "V": nome})
    d[nome] = pd.to_numeric(d[nome], errors="coerce")
    d["cod_ibge"] = d.cod_ibge.astype(int)
    d["ano"] = d.ano.astype(int)
    return d[["cod_ibge", "nome", "ano", nome]]


# ---- População --------------------------------------------------------------
pop = pd.concat([sidra(6579, 9324, "2018,2019,2020,2021,2024,2025", "pop"),
                 sidra(4709, 93, "2022", "pop")])
grade = pd.MultiIndex.from_product([sorted(pop.cod_ibge.unique()), range(2018, 2027)],
                                   names=["cod_ibge", "ano"]).to_frame(index=False)
popa = grade.merge(pop[["cod_ibge", "ano", "pop"]], how="left").sort_values(["cod_ibge", "ano"])
popa["pop"] = popa.groupby("cod_ibge")["pop"].transform(
    lambda s: s.interpolate(limit_area="inside").ffill())
popa.to_csv(PROC / "populacao_pr_ano.csv", index=False)
nomes = pop.drop_duplicates("cod_ibge").set_index("cod_ibge")["nome"]
P = popa.pivot(index="cod_ibge", columns="ano", values="pop")

# ---- PIB 2019 ---------------------------------------------------------------
pib = sidra(5938, 37, "2019", "pib_mil").set_index("cod_ibge")["pib_mil"]

# ---- SICONFI 2019 -----------------------------------------------------------
DCA = ("https://apidatalake.tesouro.gov.br/ords/siconfi/tt/dca?an_exercicio=2019"
       "&no_anexo=DCA-Anexo%20I-C&id_ente={}")
RGF = ("https://apidatalake.tesouro.gov.br/ords/siconfi/tt/rgf?an_exercicio=2019"
       "&in_periodicidade=Q&nr_periodo=3&co_tipo_demonstrativo=RGF"
       "&no_anexo=RGF-Anexo%2001&co_esfera=M&co_poder=E&id_ente={}")
DCA_D = DCA.replace("DCA-Anexo%20I-C", "DCA-Anexo%20I-D")
CONTAS = {"RO1.0.0.0.00.0.0": "rec_corrente", "RO1.1.0.0.00.0.0": "rec_tributaria",
          "RO1.3.0.0.00.0.0": "rec_patrimonial", "RO1.7.1.8.01.2.0": "fpm"}


def fiscal(cod):
    arq = BRUTOS / f"siconfi_{cod}.json"
    if arq.exists():
        return json.loads(arq.read_text())
    out = {"cod_ibge": cod}
    for x in get_json(DCA.format(cod)).get("items", []):
        if x["coluna"] == "Receitas Brutas Realizadas" and x["cod_conta"] in CONTAS:
            out[CONTAS[x["cod_conta"]]] = x["valor"]
    for x in get_json(DCA_D.format(cod)).get("items", []):
        if x["cod_conta"] == "DO3.1.00.00.00.00" and x["coluna"] == "Despesas Liquidadas":
            out["pessoal_liq"] = x["valor"]
    itens = get_json(RGF.format(cod)).get("items", [])
    if not itens:  # municípios < 50 mil hab. podem publicar o RGF por semestre
        itens = get_json(RGF.format(cod).replace("in_periodicidade=Q&nr_periodo=3",
                                                 "in_periodicidade=S&nr_periodo=2")).get("items", [])
    for x in itens:
        if x["cod_conta"] == "DespesaComPessoalTotal" and x["coluna"].startswith("% sobre a RCL"):
            out["pessoal_rcl"] = x["valor"]
        if x["cod_conta"] == "ReceitaCorrenteLiquidaLimiteLegal" and x["coluna"] == "Valor":
            out["rcl"] = x["valor"]
    if "pessoal_liq" in out and "rec_corrente" in out:  # só guarda resposta completa
        arq.write_text(json.dumps(out))
    return out


# a API às vezes devolve listas vazias: até 4 rodadas para os que faltarem
for rodada in range(4):
    with ThreadPoolExecutor(max_workers=2) as ex:
        fis = pd.DataFrame(list(ex.map(fiscal, P.index))).set_index("cod_ibge")
    if fis.reindex(columns=["pessoal_liq"]).notna().all().all():
        break
    time.sleep(30)

# ---- Distância a Curitiba -----------------------------------------------------
coord = pd.read_csv("https://raw.githubusercontent.com/kelvins/municipios-brasileiros/"
                    "main/csv/municipios.csv").set_index("codigo_ibge")
coord = coord.loc[coord.index.isin(P.index), ["latitude", "longitude"]]
lat0, lon0 = coord.loc[4106902, ["latitude", "longitude"]]      # Curitiba
la, lo = np.radians(coord.latitude), np.radians(coord.longitude)
dl = la - np.radians(lat0); dn = lo - np.radians(lon0)
h = np.sin(dl / 2) ** 2 + np.cos(la) * np.cos(np.radians(lat0)) * np.sin(dn / 2) ** 2
dist = 6371 * 2 * np.arcsin(np.sqrt(h))

cov = pd.DataFrame({"nome": nomes, "pop_2019": P[2019], "pop_2021": P[2021],
                    "pop_2022_censo": P[2022], "pop_2024": P[2024]})
cov["pib_pc_2019"] = pib * 1000 / cov.pop_2019
cov = cov.join(fis)
cov["rec_propria_pc_2019"] = (cov.rec_tributaria + cov.rec_patrimonial) / cov.pop_2019
cov["dep_fpm_2019"] = cov.fpm / cov.rec_corrente
# pessoal: DCA (todos os municípios) sobre a receita corrente; o % sobre a RCL
# do RGF só existe na API para ~1/3 dos municípios (fica como pessoal_rcl)
cov["pessoal_rc_2019"] = cov.pessoal_liq / cov.rec_corrente
cov["dist_curitiba_km"] = dist
cov.index.name = "cod_ibge"
cov.reset_index().to_csv(PROC / "covariaveis_pr.csv", index=False)
print(cov.shape)
print(cov.describe().T[["count", "mean", "min", "max"]].round(2).to_string())
