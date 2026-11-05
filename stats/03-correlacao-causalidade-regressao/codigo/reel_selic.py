# Conteúdo 3 — Estudo de caso: o reel da Selic e do déficit (Estatística e Econometria, PROFINIT)
# Execute a partir da pasta codigo/.

import pandas as pd
import statsmodels.formula.api as smf

# Base sintética do estudo (as três lições com dados simulados)
f = pd.read_excel("../../dados_caso/correlacao_causalidade_sintetica.xlsx", sheet_name="Fiscal_Selic")
f["superavit_primario"].corr(f["selic"])                        # todos: +0,82
f.groupby("regime")[["superavit_primario", "selic"]].corr()     # Simpson
smf.ols("selic ~ deficit_primario", f).fit().params             # β = −0,88
smf.ols("selic ~ deficit_primario + inflacao", f).fit().params  # β = +0,52

s = pd.read_excel("../../dados_caso/correlacao_causalidade_sintetica.xlsx", sheet_name="Sorvete_Afogamento")
s.drop(columns="semana").corr()                                 # r e correlações com a temperatura

# Tarefa: dados oficiais do SGS/BCB (pip install python-bcb)
# from bcb import sgs
# d = sgs.get({"selic": 432, "ipca": 433}, start="1999-01-01")   # confira os códigos no SGS
# Acrescente as séries de resultado primário e dívida bruta (% do PIB) e repita as contas
# em nível, em diferenças (d.diff()) e por regime de inflação.
