# Conteúdo 4 — Regressão linear múltipla
# Requer: pip install pandas numpy statsmodels
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.stats.outliers_influence import variance_inflation_factor

df = pd.read_csv("../dados/salarios.csv")
df["lsal"] = np.log(df["salario_hora"])

# (1) Regressão simples, (2) múltipla, (3) múltipla com a "habilidade"
m1 = smf.ols("lsal ~ educ", data=df).fit(cov_type="HC1")
m2 = smf.ols("lsal ~ educ + exper + I(exper**2) + mulher", data=df).fit(cov_type="HC1")
m3 = smf.ols("lsal ~ educ + exper + I(exper**2) + mulher + habilidade", data=df).fit(cov_type="HC1")
for m in (m1, m2, m3):
    print(m.params.round(4).to_dict(), "\n", m.bse.round(4).to_dict(),
          "\nR2 =", round(m.rsquared, 3), "R2aj =", round(m.rsquared_adj, 3), "n =", int(m.nobs))

# Viés de variável omitida: b_curto = b_longo + gamma * delta
delta = smf.ols("habilidade ~ educ + exper + I(exper**2) + mulher", data=df).fit().params["educ"]
print("delta =", round(delta, 4), " gamma =", round(m3.params["habilidade"], 4),
      " b_longo + gamma*delta =", round(m3.params["educ"] + m3.params["habilidade"] * delta, 4))

# Teorema de Frisch-Waugh-Lovell: "partialling out"
r_educ = smf.ols("educ ~ exper + I(exper**2) + mulher", data=df).fit().resid
print("FWL:", round(smf.ols("lsal ~ r_educ", data=df.assign(r_educ=r_educ)).fit().params["r_educ"], 4))

# Efeito marginal da experiência (modelo quadrático) e ponto de máximo
b = m2.params
print("efeito de exper aos 10 anos:", round(b["exper"] + 2 * b["I(exper ** 2)"] * 10, 4),
      " máximo em", round(-b["exper"] / (2 * b["I(exper ** 2)"]), 1), "anos")

# Teste F conjunto: exper e exper² são conjuntamente zero?
print(m2.f_test("exper = 0, I(exper ** 2) = 0"))

# Multicolinearidade: VIF
X = df[["educ", "exper", "mulher"]].assign(const=1)
print({c: round(variance_inflation_factor(X.values, i), 2) for i, c in enumerate(X.columns) if c != "const"})
