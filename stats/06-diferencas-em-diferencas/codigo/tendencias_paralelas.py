# Conteúdo 6 — Tendências paralelas: verificação (Estatística e Econometria, PROFINIT)
# Execute a partir da pasta codigo/.

import pandas as pd
import statsmodels.formula.api as smf

d = pd.read_csv("../dados/programa_saude.csv")
print(d.groupby(["ano", "tratado"])["gasto_saude_pc"].mean().unstack())   # médias por ano

pre = d[d["ano"] <= 2014].copy()
cl = {"groups": pre["municipio"]}
pre["tend"] = pre["tratado"] * (pre["ano"] - 2010)          # tendência diferencial
pre["falso"] = pre["tratado"] * (pre["ano"] >= 2012)         # placebo de data
for v in ["tend", "falso"]:
    m = smf.ols(f"gasto_saude_pc ~ {v} + C(municipio) + C(ano)", data=pre).fit(
        cov_type="cluster", cov_kwds=cl)
    print(v, round(m.params[v], 3), round(m.bse[v], 3), round(m.pvalues[v], 3))
