# Conteúdo 7 — Regressão descontínua (dados simulados: programa fictício de crédito subsidiado)
# Requer: pip install pandas numpy statsmodels rdrobust rddensity
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from rdrobust import rdrobust, rdbwselect, rdplot
from rddensity import rddensity

df = pd.read_csv("../dados/rdd_credito.csv")
df["z"] = (df["pontuacao"] - 60) / 10              # variável de corte centrada (dezenas de pontos)

# 1) Primeiro estágio: o corte aumenta a probabilidade de obter o crédito?
fs = rdrobust(df["credito"], df["z"], c=0)
print("Salto na prob. de tratamento:", round(fs.coef.iloc[0, 0], 3))

# 2) Forma reduzida (ITT): salto no investimento no corte
rf = rdrobust(df["investimento"], df["z"], c=0)
print(rf)

# 3) RDD fuzzy = forma reduzida / primeiro estágio (LATE dos compliers)
fz = rdrobust(df["investimento"], df["z"], c=0, fuzzy=df["credito"])
print(fz)
print("LATE:", round(fz.coef.iloc[0, 0], 2), " robusto IC95%:", fz.ci.iloc[2].round(2).tolist())

# 4) Mesma ideia por MQ2E "à mão" numa janela de ±20 pontos (kernel uniforme)
j = df[df["z"].abs() <= 2].copy()
j["acima_z"] = j["acima_corte"] * j["z"]
from linearmodels.iv import IV2SLS
iv = IV2SLS.from_formula("investimento ~ 1 + z + acima_z + [credito ~ acima_corte]", data=j).fit(cov_type="robust")
print("MQ2E janela ±20 pontos:", round(iv.params["credito"], 2), "(", round(iv.std_errors["credito"], 2), ")")

# 5) Validação: teste de densidade (McCrary/Cattaneo-Jansson-Ma)
dens = rddensity(X=df["z"], c=0)
print(dens.test)                                   # p_jk = p-valor robusto (jackknife)

# 6) Placebo: corte falso em 50 pontos (só empresas abaixo do corte real)
abaixo = df[df["z"] < 0]
pl = rdrobust(abaixo["investimento"], abaixo["z"], c=-1)
print("Placebo 50 pontos:", round(pl.coef.iloc[0, 0], 2), " p robusto:", round(pl.pv.iloc[2, 0], 3))

# Gráfico: rdplot(df["investimento"], df["z"], c=0)
