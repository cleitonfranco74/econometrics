# Estudos de caso — 05-dados-em-painel (Estatística e Econometria, PROFINIT)
# Execute a partir da pasta codigo/; as bases ficam em stats/dados_caso/.

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

s = pd.read_stata("../../dados_caso/samu_mt_2000_2020.dta")
s["frota_pc"] = s["frota"] / s["pop"] * 100
cl = {"groups": s["cod_mun"]}
pooled = smf.ols("tx_mortes_transito ~ samu + frota_pc + C(ano)", s).fit(cov_type="cluster", cov_kwds=cl)
fe = smf.ols("tx_mortes_transito ~ samu + frota_pc + C(cod_mun) + C(ano)", s).fit(cov_type="cluster", cov_kwds=cl)
print(pooled.params[["samu", "frota_pc"]], fe.params[["samu", "frota_pc"]])

g = pd.read_stata("../../dados_caso/gini_pib_mundo.dta")
g["lpib"] = np.log(g["gdppercapita"])
smf.ols("ginicoefficient ~ lpib + C(code) + C(year)", g).fit(
    cov_type="cluster", cov_kwds={"groups": g["code"]}).params["lpib"]
