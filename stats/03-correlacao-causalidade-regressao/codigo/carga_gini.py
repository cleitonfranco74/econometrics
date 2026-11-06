# Conteúdo 3 — Estudo de caso: carga tributária e desigualdade (Estatística e Econometria, PROFINIT)
# Execute a partir da pasta codigo/.

import pandas as pd
from scipy import stats
import statsmodels.formula.api as smf

# 37 países da OCDE e o Brasil (a mesma base está em paises_carga_gini.xlsx)
d = pd.read_csv("../../dados_caso/carga_gini_ocde_brasil.csv")
print(stats.pearsonr(d["carga_pib"], d["gini"]))                   # todos (38): r = −0,66
sem_br = d[d["pais"] != "Brasil"]
print(stats.pearsonr(sem_br["carga_pib"], sem_br["gini"]))         # sem o Brasil: −0,70
for g, x in d.groupby("grupo"):                                    # Simpson: −0,46 e +0,31
    print(g, len(x), round(x["carga_pib"].corr(x["gini"]), 2))
print(smf.ols("gini ~ carga_pib", d).fit().summary())              # reta do gráfico

# Tarefa: junte o PIB per capita (Banco Mundial, NY.GDP.PCAP.PP.KD) em uma coluna "pibpc"
# e controle por ele:  smf.ols("gini ~ carga_pib + np.log(pibpc)", d).fit().summary()
