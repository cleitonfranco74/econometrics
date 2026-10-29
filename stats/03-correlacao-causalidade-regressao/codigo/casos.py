# Estudos de caso — 03-correlacao-causalidade-regressao (Estatística e Econometria, PROFINIT)
# Execute a partir da pasta codigo/; as bases ficam em stats/dados_caso/.

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

# Sorvete e afogamentos: correlação simples e parcial
sv = pd.read_csv("../../dados_caso/sorvete_afogamentos.csv")
sv["sorvetes_mil_unid"].corr(sv["afogamentos"])
rx = smf.ols("sorvetes_mil_unid ~ temperatura_media_c", sv).fit().resid
ry = smf.ols("afogamentos ~ temperatura_media_c", sv).fit().resid
np.corrcoef(rx, ry)[0, 1]                                  # correlação parcial
smf.ols("afogamentos ~ sorvetes_mil_unid + temperatura_media_c", sv).fit().summary()

# Correlação espúria e carga tributária (com e sem pontos atípicos)
mg = pd.read_csv("../../dados_caso/margarina_divorcio_maine.csv")
mg.drop(columns="ano").corr()
ct = pd.read_csv("../../dados_caso/carga_tributaria_gini.csv")
ct["gini"].corr(ct["carga_tributaria_pib"])
sem = ct[~ct["pais"].isin(["Brasil", "Índia"])]
sem["gini"].corr(sem["carga_tributaria_pib"])

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
