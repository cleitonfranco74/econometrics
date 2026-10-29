# Estudos de caso — 03-correlacao-causalidade-regressao (Estatística e Econometria, PROFINIT)
# Execute a partir da pasta codigo/; as bases ficam em stats/dados_caso/.

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

# Correlações empresariais (uma aba por empresa)
abas = pd.read_excel("../../dados_caso/correlacoes_empresariais.xlsx", sheet_name=None)
for nome, d in abas.items():
    print(nome, d.select_dtypes("number").corr().round(3), sep="\n")

# Gini x PIB per capita
g = pd.read_stata("../../dados_caso/gini_pib_mundo.dta")
g["lpib"] = np.log(g["gdppercapita"])
u = g.sort_values("year").groupby("code").tail(1)          # observação mais recente
u[["ginicoefficient", "gdppercapita"]].corr(method="spearman")
smf.ols("ginicoefficient ~ lpib", data=u).fit(cov_type="HC1").summary()
smf.ols("ginicoefficient ~ lpib + I(lpib**2)", data=u).fit(cov_type="HC1").summary()

# Google
gg = pd.read_excel("../../dados_caso/google_reglinear.xlsx")
gg.columns = ["data", "ia", "receita", "usuarios"]
smf.ols("receita ~ ia", data=gg).fit().summary()
