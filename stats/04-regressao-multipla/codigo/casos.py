# Estudos de caso — 04-regressao-multipla (Estatística e Econometria, PROFINIT)
# Execute a partir da pasta codigo/; as bases ficam em stats/dados_caso/.

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

w = pd.read_stata("../../dados_caso/wage1.dta")
m = smf.ols("LWAGE ~ EDUC + EXPER + TENURE", data=w).fit()
m.t_test("EXPER + TENURE = 0")

p = pd.read_stata("../../dados_caso/pnad_2009_2011_internet_renda.dta", convert_categoricals=False)
p = p[p["Renda"] > 0].rename(columns={"raça": "raca"})
p["logrenda"] = np.log(p["Renda"])
smf.ols("logrenda ~ internet + lereescrever + anosestudo + C(horas_trabalhadas) + genero"
        " + idade + I(idade**2) + C(raca) + C(estcivil) + C(uf) + C(ano)", data=p).fit(cov_type="HC1")

s = pd.read_stata("../../dados_caso/samu_mt_2000_2020.dta")
s["logmortes"] = np.log(s["mortes_transito"] + 1); s["lpop"] = np.log(s["pop"])
smf.ols("logmortes ~ samu + equipamentos + ortopedista + tx_analfa + lpop", data=s).fit(
    cov_type="cluster", cov_kwds={"groups": s["cod_mun"]}).summary()

# Empresas: Y é a variável indicada no Dicionário
a = pd.read_excel("../../dados_caso/estudos_caso_regressao_multipla.xlsx", sheet_name="Amazon")
y = a["Receita de Vendas Online (bi USD)"]
X = a.drop(columns=["Data", "Receita de Vendas Online (bi USD)", "log Receitas Vendas online %"])
sm.OLS(y, sm.add_constant(X)).fit().summary()
